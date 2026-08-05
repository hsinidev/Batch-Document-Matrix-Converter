"""
High-Performance Pandoc Transcoding Engine.
Orchestrates document conversions across .txt, .docx, .epub, .html, .md, and .rtf
with CSS injection, metadata embedding, DOM sanitization, and isolated file handlers.
"""
import os
import sys
import shutil
import tempfile
import subprocess
import logging
import pypandoc
from typing import Dict, Any, Optional, List, Callable

from src.config import SUPPORTED_FORMATS, TEMP_DIR
from src.binary_resolver import PandocBinaryResolver
from src.doc_matrix import DocumentItem, ConversionStatus
from src.dublin_core import DublinCoreManager
from src.css_injector import CSSInjectorEngine
from src.dom_sanitizer import DOMSanitizer

logger = logging.getLogger("ConverterEngine")

class DocumentConverterEngine:
    """
    Main conversion pipeline coordinator.
    """

    def __init__(self, binary_resolver: PandocBinaryResolver):
        self.resolver = binary_resolver
        self.css_engine = CSSInjectorEngine()

    def convert(
        self,
        item: DocumentItem,
        output_dir: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        Executes single document transcoding pipeline synchronously.
        Returns destination output path.
        """
        options = options or {}
        pandoc_bin, ver, tier, desc = self.resolver.resolve()
        if not pandoc_bin or not os.path.isfile(pandoc_bin):
            raise RuntimeError(f"Pandoc binary unresolved. Resolution details: {desc}")

        # Ensure environment variable is set for pypandoc
        os.environ["PYPANDOC_PANDOC"] = pandoc_bin

        if progress_callback:
            progress_callback(10, f"Initializing conversion for {item.filename}...")

        output_path = item.resolve_output_path(output_dir)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        input_fmt_info = SUPPORTED_FORMATS.get(item.input_format, SUPPORTED_FORMATS["txt"])
        target_fmt_info = SUPPORTED_FORMATS.get(item.target_format, SUPPORTED_FORMATS["epub"])

        input_pandoc_fmt = input_fmt_info["pandoc"]
        target_pandoc_fmt = target_fmt_info["pandoc"]

        # Create temporary working directory for DOM preprocessing & CSS injection
        with tempfile.TemporaryDirectory(dir=TEMP_DIR, prefix="conv_job_") as job_temp_dir:
            source_file_to_convert = item.file_path

            # Step 1: Pre-process HTML or Markdown if DOM Sanitization is requested
            if item.input_format in ("html", "md") and options.get("enable_dom_sanitizer", True):
                if progress_callback:
                    progress_callback(25, "Sanitizing DOM tree and resolving media assets...")

                try:
                    with open(item.file_path, "r", encoding="utf-8", errors="replace") as f:
                        raw_content = f.read()

                    sanitizer = DOMSanitizer(options.get("sanitizer_options"))
                    clean_content, stats = sanitizer.sanitize_html(raw_content, os.path.dirname(item.file_path))

                    # Inject frontmatter metadata into HTML/Markdown source
                    clean_content = DublinCoreManager.inject_frontmatter_to_text(clean_content, item.metadata)

                    temp_source = os.path.join(job_temp_dir, f"sanitized_input.{item.input_ext.lstrip('.')}")
                    with open(temp_source, "w", encoding="utf-8") as f:
                        f.write(clean_content)

                    source_file_to_convert = temp_source
                except Exception as e:
                    logger.warning(f"DOM preprocessing failed, falling back to raw file: {e}")

            # Step 2: Prepare CSS injection file
            css_args = []
            if item.target_format in ("html", "epub"):
                if progress_callback:
                    progress_callback(40, "Preparing CSS typography stylesheet injection...")

                css_content = ""
                selected_preset = options.get("css_preset")
                if selected_preset:
                    css_content = self.css_engine.get_preset_content(selected_preset)
                elif options.get("custom_css_text"):
                    css_content = options.get("custom_css_text", "")

                if css_content:
                    injected_css_path = self.css_engine.generate_custom_css_file(
                        base_css_content=css_content,
                        output_temp_dir=job_temp_dir,
                        font_family=options.get("override_font_family"),
                        font_size_pt=options.get("override_font_size"),
                        margin_em=options.get("override_margin")
                    )
                    css_args = self.css_engine.get_pandoc_css_args(injected_css_path)

            # Step 3: Build Metadata parameters
            if progress_callback:
                progress_callback(60, "Building Dublin Core metadata parameters...")
            metadata_args = DublinCoreManager.build_pandoc_args(item.metadata)

            # Step 4: Assemble extra Pandoc CLI options
            extra_args = ["--standalone"]
            if options.get("generate_toc", True) and item.target_format in ("html", "epub", "docx", "md"):
                extra_args.append("--toc")

            extra_args.extend(css_args)
            extra_args.extend(metadata_args)
            
            # Additional custom user flags
            if item.custom_flags:
                extra_args.extend(item.custom_flags)

            # Step 5: Execute Pandoc Conversion
            if progress_callback:
                progress_callback(75, f"Transcoding {item.input_format.upper()} -> {item.target_format.upper()} via Pandoc...")

            cmd = [
                pandoc_bin,
                source_file_to_convert,
                "-f", input_pandoc_fmt,
                "-t", target_pandoc_fmt,
                "-o", output_path
            ] + extra_args

            logger.info(f"Executing Pandoc command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            if result.returncode != 0:
                err_msg = result.stderr.strip() if result.stderr else "Pandoc process returned non-zero code."
                raise RuntimeError(f"Pandoc transcoding failed: {err_msg}")

            if progress_callback:
                progress_callback(100, f"Successfully created {os.path.basename(output_path)}")

        return output_path
