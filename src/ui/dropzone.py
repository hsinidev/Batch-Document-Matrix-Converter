"""
Drag and Drop File Matrix Queue UI Component.
"""
import os
import customtkinter as ctk
from tkinter import filedialog
from typing import List, Callable, Optional, Dict

from src.config import SUPPORTED_FORMATS, VALID_EXTENSIONS
from src.doc_matrix import DocumentItem, ConversionStatus
from src.ui.theme import UIStyle

class DocumentMatrixQueueView(ctk.CTkFrame):
    """
    Dual drag-and-drop zone and scrollable batch file queue matrix.
    """

    def __init__(
        self,
        master,
        on_files_added: Callable[[List[str]], None],
        on_item_select: Callable[[DocumentItem], None],
        on_item_delete: Callable[[DocumentItem], None],
        on_convert_click: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color=UIStyle.BG_SECONDARY, corner_radius=10, **kwargs)
        
        self.on_files_added = on_files_added
        self.on_item_select = on_item_select
        self.on_item_delete = on_item_delete
        self.on_convert_click = on_convert_click
        
        self.items: List[DocumentItem] = []
        self.selected_item: Optional[DocumentItem] = None
        self._row_widgets: Dict[str, dict] = {}

        self._build_ui()

    def _build_ui(self):
        # 1. Header Action Bar
        header_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8, height=50)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Document Conversion Matrix",
            font=UIStyle.FONT_SUBHEADING,
            text_color=UIStyle.TEXT_PRIMARY
        )
        title_lbl.pack(side="left", padx=15, pady=10)

        # Global Target Format Selector
        fmt_lbl = ctk.CTkLabel(header_frame, text="Global Target:", font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_SECONDARY)
        fmt_lbl.pack(side="left", padx=(20, 5))

        self.global_target_combo = ctk.CTkComboBox(
            header_frame,
            values=[fmt.upper() for fmt in SUPPORTED_FORMATS.keys()],
            width=100,
            command=self._on_global_format_change,
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER,
            button_color=UIStyle.ACCENT_PRIMARY
        )
        self.global_target_combo.set("EPUB")
        self.global_target_combo.pack(side="left", padx=5)

        # Add Files Button
        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Files",
            width=100,
            fg_color=UIStyle.ACCENT_PRIMARY,
            hover_color=UIStyle.ACCENT_HOVER,
            command=self._open_file_dialog
        )
        add_btn.pack(side="right", padx=10, pady=10)

        # Add Folder Button
        folder_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Folder",
            width=100,
            fg_color=UIStyle.SURFACE_CARD,
            border_color=UIStyle.ACCENT_SECONDARY,
            border_width=1,
            hover_color=UIStyle.BG_PRIMARY,
            text_color=UIStyle.ACCENT_SECONDARY,
            command=self._open_folder_dialog
        )
        folder_btn.pack(side="right", padx=5)

        # 2. Drag & Drop Target Area
        self.drop_area = ctk.CTkFrame(
            self,
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.ACCENT_PRIMARY,
            border_width=2,
            corner_radius=10,
            height=80
        )
        self.drop_area.pack(fill="x", padx=10, pady=5)
        self.drop_area.pack_propagate(False)

        drop_lbl = ctk.CTkLabel(
            self.drop_area,
            text="📥  Drag & Drop Documents Here (.txt, .docx, .epub, .html, .md, .rtf)",
            font=UIStyle.FONT_BODY_BOLD,
            text_color=UIStyle.TEXT_SECONDARY
        )
        drop_lbl.pack(expand=True)

        # Register TkinterDnD drop if supported by root window
        try:
            self.drop_area.drop_target_register("DND_Files")
            self.drop_area.dnd_bind("<<Drop>>", self._handle_dnd_drop)
        except Exception:
            pass  # Fallback gracefully if TkinterDnD2 native binding is unavailable

        # 3. Queue Matrix Table Header
        matrix_header = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, height=30, corner_radius=4)
        matrix_header.pack(fill="x", padx=10, pady=(5, 0))

        headers = [
            ("File Name", 0.35),
            ("Input", 0.10),
            ("Target", 0.12),
            ("Size", 0.10),
            ("Status", 0.18),
            ("Actions", 0.15)
        ]
        for title, weight in headers:
            col_lbl = ctk.CTkLabel(
                matrix_header,
                text=title,
                font=UIStyle.FONT_CAPTION,
                text_color=UIStyle.TEXT_SECONDARY,
                anchor="w"
            )
            col_lbl.pack(side="left", expand=True, fill="x", padx=5)

        # 4. Scrollable Document Queue Table
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER,
            border_width=1,
            corner_radius=8
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Empty state label
        self.empty_lbl = ctk.CTkLabel(
            self.scroll_frame,
            text="No documents in queue. Drag & drop files or click '+ Add Files' to begin.",
            font=UIStyle.FONT_BODY,
            text_color=UIStyle.TEXT_SECONDARY
        )
        self.empty_lbl.pack(pady=40)

        # 5. Bottom Action Controls
        bottom_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8, height=45)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.queue_info_lbl = ctk.CTkLabel(
            bottom_frame,
            text="0 Documents in Queue",
            font=UIStyle.FONT_CAPTION,
            text_color=UIStyle.TEXT_SECONDARY
        )
        self.queue_info_lbl.pack(side="left", padx=15)

        clear_btn = ctk.CTkButton(
            bottom_frame,
            text="Clear Queue",
            width=90,
            fg_color="transparent",
            text_color=UIStyle.DANGER,
            hover_color=UIStyle.BG_PRIMARY,
            command=self._clear_queue
        )
        clear_btn.pack(side="right", padx=10)

        self.convert_btn = ctk.CTkButton(
            bottom_frame,
            text="⚡ Start Batch Transcoding",
            font=UIStyle.FONT_BODY_BOLD,
            width=180,
            fg_color=UIStyle.ACCENT_PRIMARY,
            hover_color=UIStyle.ACCENT_HOVER,
            command=self.on_convert_click
        )
        self.convert_btn.pack(side="right", padx=5, pady=5)

    def set_items(self, items: List[DocumentItem]):
        self.items = items
        self._refresh_matrix_table()

    def add_files(self, paths: List[str]):
        valid_paths = []
        for path in paths:
            path = path.strip("{}'\"")
            if os.path.isfile(path):
                _, ext = os.path.splitext(path)
                if ext.lower() in VALID_EXTENSIONS:
                    valid_paths.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        _, ext = os.path.splitext(f)
                        if ext.lower() in VALID_EXTENSIONS:
                            valid_paths.append(os.path.join(root, f))
        if valid_paths:
            self.on_files_added(valid_paths)

    def _handle_dnd_drop(self, event):
        raw_data = event.data
        # Parse dropped file paths
        paths = self.master.tk.splitlist(raw_data)
        self.add_files(list(paths))

    def _open_file_dialog(self):
        ext_pattern = " ".join([f"*{ext}" for ext in VALID_EXTENSIONS])
        files = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[("Supported Documents", ext_pattern), ("All Files", "*.*")]
        )
        if files:
            self.add_files(list(files))

    def _open_folder_dialog(self):
        folder = filedialog.askdirectory(title="Select Document Folder")
        if folder:
            self.add_files([folder])

    def _on_global_format_change(self, choice: str):
        target_fmt = choice.lower()
        for item in self.items:
            item.target_format = target_fmt
        self._refresh_matrix_table()

    def _clear_queue(self):
        self.items.clear()
        self._refresh_matrix_table()

    def _refresh_matrix_table(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self._row_widgets.clear()

        if not self.items:
            self.empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="No documents in queue. Drag & drop files or click '+ Add Files' to begin.",
                font=UIStyle.FONT_BODY,
                text_color=UIStyle.TEXT_SECONDARY
            )
            self.empty_lbl.pack(pady=40)
            self.queue_info_lbl.configure(text="0 Documents in Queue")
            return

        self.queue_info_lbl.configure(text=f"{len(self.items)} Document(s) in Queue")

        for item in self.items:
            row_frame = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=UIStyle.SURFACE_CARD if self.selected_item != item else UIStyle.BG_SECONDARY,
                corner_radius=6,
                height=40,
                border_color=UIStyle.ACCENT_PRIMARY if self.selected_item == item else UIStyle.BORDER,
                border_width=1
            )
            row_frame.pack(fill="x", pady=2, padx=2)

            # Highlight select event
            row_frame.bind("<Button-1>", lambda e, it=item: self._select_row(it))

            # 1. Filename & icon
            name_lbl = ctk.CTkLabel(
                row_frame,
                text=f"📄 {item.filename}",
                font=UIStyle.FONT_BODY,
                text_color=UIStyle.TEXT_PRIMARY,
                anchor="w"
            )
            name_lbl.pack(side="left", expand=True, fill="x", padx=10)

            # 2. Input Format badge
            in_badge = ctk.CTkLabel(
                row_frame,
                text=item.input_format.upper(),
                font=UIStyle.FONT_CAPTION,
                fg_color=UIStyle.BG_PRIMARY,
                text_color=UIStyle.ACCENT_SECONDARY,
                corner_radius=4,
                width=50
            )
            in_badge.pack(side="left", padx=5)

            # 3. Target Format Combo
            target_combo = ctk.CTkComboBox(
                row_frame,
                values=[fmt.upper() for fmt in SUPPORTED_FORMATS.keys()],
                width=75,
                height=24,
                fg_color=UIStyle.BG_PRIMARY,
                command=lambda val, it=item: self._on_item_target_change(it, val)
            )
            target_combo.set(item.target_format.upper())
            target_combo.pack(side="left", padx=5)

            # 4. File Size
            size_lbl = ctk.CTkLabel(
                row_frame,
                text=item.formatted_size(),
                font=UIStyle.FONT_CAPTION,
                text_color=UIStyle.TEXT_SECONDARY,
                width=65
            )
            size_lbl.pack(side="left", padx=5)

            # 5. Status Badge & Progress
            status_color = UIStyle.TEXT_SECONDARY
            if item.status == ConversionStatus.COMPLETED:
                status_color = UIStyle.SUCCESS
            elif item.status == ConversionStatus.FAILED:
                status_color = UIStyle.DANGER
            elif item.status == ConversionStatus.PROCESSING:
                status_color = UIStyle.ACCENT_PRIMARY

            status_lbl = ctk.CTkLabel(
                row_frame,
                text=item.status,
                font=UIStyle.FONT_CAPTION,
                text_color=status_color,
                width=80
            )
            status_lbl.pack(side="left", padx=5)

            # 6. Action buttons
            edit_btn = ctk.CTkButton(
                row_frame,
                text="✏️ Edit",
                width=50,
                height=24,
                fg_color=UIStyle.BG_PRIMARY,
                text_color=UIStyle.TEXT_PRIMARY,
                hover_color=UIStyle.ACCENT_PRIMARY,
                command=lambda it=item: self._select_row(it)
            )
            edit_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                row_frame,
                text="❌",
                width=30,
                height=24,
                fg_color="transparent",
                text_color=UIStyle.DANGER,
                hover_color=UIStyle.BG_PRIMARY,
                command=lambda it=item: self._remove_item(it)
            )
            del_btn.pack(side="left", padx=2)

            self._row_widgets[item.id] = {
                "frame": row_frame,
                "status_lbl": status_lbl,
                "combo": target_combo
            }

    def update_item_status(self, doc_id: str, status: str):
        for item in self.items:
            if item.id == doc_id:
                item.status = status
                if doc_id in self._row_widgets:
                    lbl = self._row_widgets[doc_id]["status_lbl"]
                    color = UIStyle.TEXT_SECONDARY
                    if status == ConversionStatus.COMPLETED:
                        color = UIStyle.SUCCESS
                    elif status == ConversionStatus.FAILED:
                        color = UIStyle.DANGER
                    elif status == ConversionStatus.PROCESSING:
                        color = UIStyle.ACCENT_PRIMARY
                    lbl.configure(text=status, text_color=color)

    def _select_row(self, item: DocumentItem):
        self.selected_item = item
        self._refresh_matrix_table()
        self.on_item_select(item)

    def _on_item_target_change(self, item: DocumentItem, val: str):
        item.target_format = val.lower()

    def _remove_item(self, item: DocumentItem):
        if item in self.items:
            self.items.remove(item)
            if self.selected_item == item:
                self.selected_item = None
            self._refresh_matrix_table()
            self.on_item_delete(item)
