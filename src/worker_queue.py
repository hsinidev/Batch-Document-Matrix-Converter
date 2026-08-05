"""
Sequential Memory-Safe Pipeline & Thread Worker Queue.
Executes document transcoding jobs sequentially on a background thread,
streaming atomic telemetry payloads to the CustomTkinter GUI thread via queue.Queue.
"""
import queue
import threading
import logging
import time
import os
from typing import Dict, Any, List, Optional, Tuple

from src.doc_matrix import DocumentItem, ConversionStatus
from src.converter_engine import DocumentConverterEngine
from src.binary_resolver import PandocBinaryResolver

logger = logging.getLogger("WorkerQueue")

class SequentialConversionWorker:
    """
    Sequential background queue worker.
    Guarantees zero Pandoc memory leaks or OS file handle lockups by processing documents strictly 1-by-1.
    """

    def __init__(self, converter_engine: DocumentConverterEngine):
        self.engine = converter_engine
        self.job_queue: queue.Queue = queue.Queue()
        self.telemetry_queue: queue.Queue = queue.Queue()
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._current_item: Optional[DocumentItem] = None

    def start(self):
        if self._is_running:
            return
        self._stop_event.clear()
        self._is_running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="PandocWorkerThread")
        self._thread.start()
        logger.info("Sequential Conversion Worker thread started.")

    def stop(self):
        self._stop_event.set()
        self._is_running = False
        # Clear remaining jobs
        while not self.job_queue.empty():
            try:
                self.job_queue.get_nowait()
                self.job_queue.task_done()
            except queue.Empty:
                break
        logger.info("Sequential Conversion Worker stopped.")

    def add_job(self, item: DocumentItem, output_dir: Optional[str], options: Dict[str, Any]):
        """
        Enqueues a conversion job.
        """
        item.update_status(ConversionStatus.QUEUED, 0)
        self.job_queue.put((item, output_dir, options))
        self.telemetry_queue.put(('STATUS', item.id, ConversionStatus.QUEUED))
        self.telemetry_queue.put(('LOG', 'INFO', f"Enqueued '{item.filename}' for conversion to {item.target_format.upper()}."))

    def cancel_current_or_all(self):
        """
        Signals worker to cancel execution.
        """
        self._stop_event.set()
        if self._current_item:
            self._current_item.update_status(ConversionStatus.CANCELLED, 0, "Job cancelled by user.")
            self.telemetry_queue.put(('STATUS', self._current_item.id, ConversionStatus.CANCELLED))
            self.telemetry_queue.put(('LOG', 'WARN', f"Cancelled conversion for '{self._current_item.filename}'."))

    def _worker_loop(self):
        processed_count = 0
        success_count = 0

        while not self._stop_event.is_set():
            try:
                job = self.job_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            item, output_dir, options = job
            self._current_item = item

            if self._stop_event.is_set():
                item.update_status(ConversionStatus.CANCELLED, 0, "Queue stopped.")
                self.telemetry_queue.put(('STATUS', item.id, ConversionStatus.CANCELLED))
                self.job_queue.task_done()
                continue

            processed_count += 1
            item.update_status(ConversionStatus.PROCESSING, 5)
            self.telemetry_queue.put(('STATUS', item.id, ConversionStatus.PROCESSING))
            self.telemetry_queue.put(('PROGRESS', 5, item.filename))
            self.telemetry_queue.put(('LOG', 'INFO', f"Started processing '{item.filename}'..."))

            def progress_cb(percent: int, message: str):
                item.progress = percent
                self.telemetry_queue.put(('PROGRESS', percent, item.filename))
                self.telemetry_queue.put(('LOG', 'INFO', f"[{item.filename}] {message}"))

            try:
                output_file = self.engine.convert(
                    item=item,
                    output_dir=output_dir,
                    options=options,
                    progress_callback=progress_cb
                )

                item.update_status(ConversionStatus.COMPLETED, 100)
                success_count += 1
                self.telemetry_queue.put(('STATUS', item.id, ConversionStatus.COMPLETED))
                self.telemetry_queue.put(('COMPLETE', item.id, output_file))
                self.telemetry_queue.put(('LOG', 'SUCCESS', f"Completed conversion: '{item.filename}' -> '{os.path.basename(output_file)}'"))

            except Exception as e:
                err_msg = str(e)
                logger.error(f"Error converting '{item.filename}': {err_msg}")
                item.update_status(ConversionStatus.FAILED, 0, err_msg)
                self.telemetry_queue.put(('STATUS', item.id, ConversionStatus.FAILED))
                self.telemetry_queue.put(('ERROR', item.id, err_msg))
                self.telemetry_queue.put(('LOG', 'ERROR', f"Failed '{item.filename}': {err_msg}"))

            finally:
                self._current_item = None
                self.job_queue.task_done()
                time.sleep(0.05)  # Yield brief interval between process handles

        self.telemetry_queue.put(('QUEUE_FINISHED', processed_count, success_count))

    def is_busy(self) -> bool:
        return self._current_item is not None or not self.job_queue.empty()
