"""
Master MainWindow Layout & CustomTkinter Event Loop Coordinator.
Integrates file dropzone matrix, Dublin Core inspector, CSS injector,
DOM sanitizer controls, Pandoc engine status, and 20 Hz (50ms) telemetry queue polling.
"""
import os
import queue
import customtkinter as ctk
from tkinter import filedialog
from typing import List, Optional, Dict, Any

from src.config import APP_NAME, APP_VERSION, SUPPORTED_FORMATS
from src.binary_resolver import PandocBinaryResolver
from src.doc_matrix import DocumentItem, ConversionStatus
from src.converter_engine import DocumentConverterEngine
from src.worker_queue import SequentialConversionWorker
from src.css_injector import CSSInjectorEngine

from src.ui.theme import setup_app_theme, UIStyle
from src.ui.dropzone import DocumentMatrixQueueView
from src.ui.metadata_panel import MetadataEditorPanel
from src.ui.css_panel import CSSInjectorPanel
from src.ui.sanitizer_panel import SanitizerOptionsPanel
from src.ui.engine_panel import EngineStatusPanel
from src.ui.log_panel import LogConsolePanel

class MainWindow(ctk.CTk):
    """
    Main Application Window.
    """

    def __init__(self):
        super().__init__()
        setup_app_theme()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x850")
        self.minsize(1024, 700)
        self.configure(fg_color=UIStyle.BG_PRIMARY)

        # Core Engines & State
        self.resolver = PandocBinaryResolver()
        self.resolver.resolve()
        self.converter_engine = DocumentConverterEngine(self.resolver)
        self.worker = SequentialConversionWorker(self.converter_engine)
        self.worker.start()

        self.document_items: List[DocumentItem] = []
        self.output_directory: Optional[str] = None

        self._build_ui()
        
        # Start 20 Hz (50ms) telemetry queue polling loop
        self.after(50, self._poll_telemetry_queue)

    def _build_ui(self):
        # 1. Header Bar
        header_bar = ctk.CTkFrame(self, fg_color=UIStyle.BG_SECONDARY, corner_radius=0, height=60)
        header_bar.pack(fill="x", side="top")

        title_lbl = ctk.CTkLabel(
            header_bar,
            text=f"⚡ {APP_NAME}",
            font=UIStyle.FONT_HEADING,
            text_color=UIStyle.TEXT_PRIMARY
        )
        title_lbl.pack(side="left", padx=20, pady=15)

        ver_badge = ctk.CTkLabel(
            header_bar,
            text=APP_VERSION,
            font=UIStyle.FONT_CAPTION,
            fg_color=UIStyle.SURFACE_CARD,
            text_color=UIStyle.ACCENT_SECONDARY,
            corner_radius=4,
            width=80
        )
        ver_badge.pack(side="left", padx=5)

        # Output Folder Picker
        out_lbl = ctk.CTkLabel(header_bar, text="Output Directory:", font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_SECONDARY)
        out_lbl.pack(side="left", padx=(30, 5))

        self.out_dir_entry = ctk.CTkEntry(
            header_bar,
            placeholder_text="Default: Same folder as source file",
            width=260,
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER
        )
        self.out_dir_entry.pack(side="left", padx=5)

        out_browse_btn = ctk.CTkButton(
            header_bar,
            text="Choose Output...",
            width=110,
            fg_color=UIStyle.SURFACE_CARD,
            border_color=UIStyle.ACCENT_PRIMARY,
            border_width=1,
            hover_color=UIStyle.ACCENT_PRIMARY,
            command=self._choose_output_directory
        )
        out_browse_btn.pack(side="left", padx=5)

        # Pandoc Engine Indicator Pill
        self.engine_pill = ctk.CTkButton(
            header_bar,
            text="Checking Pandoc...",
            font=UIStyle.FONT_CAPTION,
            fg_color=UIStyle.SURFACE_CARD,
            text_color=UIStyle.WARNING,
            hover_color=UIStyle.BG_PRIMARY,
            command=self._switch_to_engine_tab
        )
        self.engine_pill.pack(side="right", padx=20)
        self._update_engine_pill()

        # 2. Main Content Split View
        main_paned = ctk.CTkFrame(self, fg_color="transparent")
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Pane: Document Matrix Queue (70% width)
        self.queue_view = DocumentMatrixQueueView(
            main_paned,
            on_files_added=self._on_files_added,
            on_item_select=self._on_item_selected,
            on_item_delete=self._on_item_deleted,
            on_convert_click=self._start_batch_conversion
        )
        self.queue_view.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Right Pane: Tabbed Control Inspector (30% width)
        self.tabview = ctk.CTkTabview(
            main_paned,
            width=420,
            fg_color=UIStyle.BG_SECONDARY,
            segmented_button_fg_color=UIStyle.SURFACE_CARD,
            segmented_button_selected_color=UIStyle.ACCENT_PRIMARY,
            segmented_button_selected_hover_color=UIStyle.ACCENT_HOVER
        )
        self.tabview.pack(side="right", fill="both", padx=(5, 0))

        tab_meta = self.tabview.add("Dublin Core")
        tab_css = self.tabview.add("CSS Styling")
        tab_dom = self.tabview.add("DOM Sanitizer")
        tab_eng = self.tabview.add("Pandoc Engine")

        # Tab 1: Dublin Core Metadata Editor
        self.meta_panel = MetadataEditorPanel(tab_meta, on_metadata_changed=self._on_metadata_changed)
        self.meta_panel.pack(fill="both", expand=True)

        # Tab 2: CSS Typography Injector
        self.css_panel = CSSInjectorPanel(tab_css, css_engine=self.converter_engine.css_engine, on_css_options_changed=self._on_css_changed)
        self.css_panel.pack(fill="both", expand=True)

        # Tab 3: DOM Sanitizer & Pandoc Flags
        self.sanitizer_panel = SanitizerOptionsPanel(tab_dom, on_options_changed=self._on_sanitizer_changed)
        self.sanitizer_panel.pack(fill="both", expand=True)

        # Tab 4: Pandoc Engine Status
        self.engine_panel = EngineStatusPanel(tab_eng, resolver=self.resolver, on_resolver_updated=self._update_engine_pill)
        self.engine_panel.pack(fill="both", expand=True)

        # 3. Bottom Section: Telemetry Log Console & Progress Bar
        bottom_box = ctk.CTkFrame(self, fg_color=UIStyle.BG_SECONDARY, corner_radius=8, height=180)
        bottom_box.pack(fill="x", side="bottom", padx=10, pady=(0, 10))

        # Progress Bar Bar
        progress_bar_frame = ctk.CTkFrame(bottom_box, fg_color="transparent")
        progress_bar_frame.pack(fill="x", padx=10, pady=(5, 2))

        self.progress_lbl = ctk.CTkLabel(progress_bar_frame, text="Ready", font=UIStyle.FONT_CAPTION, text_color=UIStyle.TEXT_SECONDARY)
        self.progress_lbl.pack(side="left")

        self.progressbar = ctk.CTkProgressBar(
            progress_bar_frame,
            progress_color=UIStyle.ACCENT_PRIMARY,
            fg_color=UIStyle.BG_PRIMARY,
            height=8
        )
        self.progressbar.set(0.0)
        self.progressbar.pack(side="right", expand=True, fill="x", padx=10)

        # Log Console
        self.log_panel = LogConsolePanel(bottom_box, height=140)
        self.log_panel.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.log_panel.log("INFO", f"{APP_NAME} v{APP_VERSION} initialized successfully.")

    def _choose_output_directory(self):
        folder = filedialog.askdirectory(title="Select Output Destination Directory")
        if folder:
            self.output_directory = folder
            self.out_dir_entry.delete(0, "end")
            self.out_dir_entry.insert(0, folder)
            self.log_panel.log("INFO", f"Set output directory to: {folder}")

    def _update_engine_pill(self):
        info = self.resolver.get_info()
        if info["is_valid"]:
            self.engine_pill.configure(
                text=f"⚙️ Pandoc v{info['version']} ({info['details'].split(':')[0]})",
                text_color=UIStyle.SUCCESS
            )
        else:
            self.engine_pill.configure(
                text="⚠️ Pandoc Unresolved (Click)",
                text_color=UIStyle.DANGER
            )

    def _switch_to_engine_tab(self):
        self.tabview.set("Pandoc Engine")

    def _on_files_added(self, paths: List[str]):
        new_items = []
        for path in paths:
            # Check if file is already queued
            if not any(item.file_path == path for item in self.document_items):
                item = DocumentItem(file_path=path, target_format=self.queue_view.global_target_combo.get().lower())
                self.document_items.append(item)
                new_items.append(item)

        if new_items:
            self.queue_view.set_items(self.document_items)
            self.log_panel.log("INFO", f"Added {len(new_items)} document(s) to matrix queue.")

    def _on_item_selected(self, item: DocumentItem):
        self.meta_panel.load_item(item)

    def _on_item_deleted(self, item: DocumentItem):
        if item in self.document_items:
            self.document_items.remove(item)
        self.log_panel.log("INFO", f"Removed '{item.filename}' from queue.")

    def _on_metadata_changed(self, metadata: Dict[str, Any], apply_to_all: bool):
        if apply_to_all:
            for item in self.document_items:
                item.metadata.update(metadata)
            self.log_panel.log("INFO", "Applied Dublin Core metadata to ALL queue items.")
        else:
            if self.queue_view.selected_item:
                self.queue_view.selected_item.metadata.update(metadata)
                self.log_panel.log("INFO", f"Updated metadata for '{self.queue_view.selected_item.filename}'.")

    def _on_css_changed(self, options: Dict[str, Any]):
        pass

    def _on_sanitizer_changed(self, options: Dict[str, Any]):
        pass

    def _start_batch_conversion(self):
        if not self.document_items:
            self.log_panel.log("WARN", "No documents in queue to convert.")
            return

        info = self.resolver.get_info()
        if not info["is_valid"]:
            self.log_panel.log("ERROR", "Cannot start conversion: Pandoc binary is unresolved.")
            self._switch_to_engine_tab()
            return

        out_dir = self.out_dir_entry.get().strip() or None
        options = {}
        options.update(self.css_panel.get_options())
        options.update(self.sanitizer_panel.get_options())

        self.progressbar.set(0.0)
        self.progress_lbl.configure(text="Batch Transcoding Started...")
        self.log_panel.log("INFO", f"Starting batch conversion of {len(self.document_items)} file(s)...")

        for item in self.document_items:
            self.worker.add_job(item, out_dir, options)

    def _poll_telemetry_queue(self):
        """
        20 Hz (50ms) polling callback consuming telemetry events from sequential worker thread.
        """
        try:
            while True:
                payload = self.worker.telemetry_queue.get_nowait()
                msg_type = payload[0]

                if msg_type == 'STATUS':
                    _, doc_id, state = payload
                    self.queue_view.update_item_status(doc_id, state)

                elif msg_type == 'PROGRESS':
                    _, percent, filename = payload
                    self.progressbar.set(percent / 100.0)
                    self.progress_lbl.configure(text=f"[{percent}%] Processing {filename}...")

                elif msg_type == 'LOG':
                    _, level, text = payload
                    self.log_panel.log(level, text)

                elif msg_type == 'COMPLETE':
                    pass

                elif msg_type == 'ERROR':
                    pass

                elif msg_type == 'QUEUE_FINISHED':
                    _, total, success = payload
                    self.progressbar.set(1.0)
                    self.progress_lbl.configure(text=f"Batch Finished ({success}/{total} successful)")
                    self.log_panel.log("SUCCESS", f"✨ Batch transcoding finished: {success}/{total} documents completed.")

                self.worker.telemetry_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(50, self._poll_telemetry_queue)

    def on_closing(self):
        self.worker.stop()
        self.destroy()
