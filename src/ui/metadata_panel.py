"""
Dublin Core Metadata Batch Editor UI Panel.
Allows inspecting and updating Dublin Core metadata fields across document items.
"""
import os
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from typing import Optional, Callable, Dict, Any

from src.doc_matrix import DocumentItem
from src.dublin_core import DublinCoreManager
from src.ui.theme import UIStyle

class MetadataEditorPanel(ctk.CTkFrame):
    """
    Interactive Dublin Core metadata inspector with cover image preview.
    """

    def __init__(
        self,
        master,
        on_metadata_changed: Callable[[Dict[str, Any], bool], None],
        **kwargs
    ):
        super().__init__(master, fg_color=UIStyle.BG_SECONDARY, corner_radius=10, **kwargs)
        self.on_metadata_changed = on_metadata_changed
        self.current_item: Optional[DocumentItem] = None
        self._cover_ctk_img = None

        self._build_ui()

    def _build_ui(self):
        title_lbl = ctk.CTkLabel(
            self,
            text="Dublin Core Metadata Inspector",
            font=UIStyle.FONT_SUBHEADING,
            text_color=UIStyle.ACCENT_PRIMARY
        )
        title_lbl.pack(anchor="w", padx=15, pady=(15, 5))

        self.subtitle_lbl = ctk.CTkLabel(
            self,
            text="Select a document from the queue to edit metadata.",
            font=UIStyle.FONT_CAPTION,
            text_color=UIStyle.TEXT_SECONDARY
        )
        self.subtitle_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Form Scrollable Container
        form_frame = ctk.CTkScrollableFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        form_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Document Title
        self.title_entry = self._create_field(form_frame, "Document Title:", "e.g. User Guide & Technical Manual")

        # 2. Creator / Author
        self.author_entry = self._create_field(form_frame, "Author / Creator:", "e.g. Jane Doe")

        # 3. Publisher
        self.publisher_entry = self._create_field(form_frame, "Publisher:", "e.g. Acme Publishing House")

        # 4. Language Code
        lang_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        lang_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(lang_frame, text="Language (RFC 5646):", font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_PRIMARY).pack(anchor="w")
        self.lang_combo = ctk.CTkComboBox(
            lang_frame,
            values=["en-US", "en-GB", "zh-CN", "zh-TW", "ja-JP", "de-DE", "fr-FR", "es-ES"],
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER
        )
        self.lang_combo.set("en-US")
        self.lang_combo.pack(fill="x", pady=(2, 0))

        # 5. Subject / Keywords
        self.subject_entry = self._create_field(form_frame, "Subject / Keywords:", "e.g. Software, Pandoc, Transcoding")

        # 6. Rights / Copyright
        self.rights_entry = self._create_field(form_frame, "Rights / Copyright:", "e.g. Copyright © 2026. All Rights Reserved.")

        # 7. Cover Image File Selector & Preview
        cover_frame = ctk.CTkFrame(form_frame, fg_color=UIStyle.BG_PRIMARY, corner_radius=6)
        cover_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(cover_frame, text="EPUB Cover Image:", font=UIStyle.FONT_BODY_BOLD, text_color=UIStyle.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(8, 2))

        browse_row = ctk.CTkFrame(cover_frame, fg_color="transparent")
        browse_row.pack(fill="x", padx=10, pady=2)

        self.cover_path_entry = ctk.CTkEntry(
            browse_row,
            placeholder_text="No cover image selected (.jpg, .png)",
            fg_color=UIStyle.SURFACE_CARD,
            border_color=UIStyle.BORDER
        )
        self.cover_path_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

        cover_browse_btn = ctk.CTkButton(
            browse_row,
            text="Browse...",
            width=70,
            fg_color=UIStyle.ACCENT_PRIMARY,
            hover_color=UIStyle.ACCENT_HOVER,
            command=self._browse_cover_image
        )
        cover_browse_btn.pack(side="right")

        # Cover Thumbnail Widget
        self.cover_preview_lbl = ctk.CTkLabel(
            cover_frame,
            text="[ No Cover Image Preview ]",
            font=UIStyle.FONT_CAPTION,
            text_color=UIStyle.TEXT_SECONDARY,
            height=100
        )
        self.cover_preview_lbl.pack(pady=8)

        # 8. Bottom Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        btn_frame.pack(fill="x", padx=10, pady=10)

        apply_sel_btn = ctk.CTkButton(
            btn_frame,
            text="Save to Selected",
            font=UIStyle.FONT_BODY_BOLD,
            fg_color=UIStyle.ACCENT_PRIMARY,
            hover_color=UIStyle.ACCENT_HOVER,
            command=lambda: self._apply_metadata(apply_to_all=False)
        )
        apply_sel_btn.pack(side="left", expand=True, fill="x", padx=5, pady=8)

        apply_all_btn = ctk.CTkButton(
            btn_frame,
            text="Apply to All Batch Items",
            font=UIStyle.FONT_BODY,
            fg_color=UIStyle.SURFACE_CARD,
            border_color=UIStyle.ACCENT_SECONDARY,
            border_width=1,
            text_color=UIStyle.ACCENT_SECONDARY,
            hover_color=UIStyle.BG_PRIMARY,
            command=lambda: self._apply_metadata(apply_to_all=True)
        )
        apply_all_btn.pack(side="right", expand=True, fill="x", padx=5, pady=8)

    def _create_field(self, parent, label_text: str, placeholder: str) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        lbl = ctk.CTkLabel(frame, text=label_text, font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_PRIMARY)
        lbl.pack(anchor="w")
        entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER
        )
        entry.pack(fill="x", pady=(2, 0))
        return entry

    def load_item(self, item: Optional[DocumentItem]):
        self.current_item = item
        if not item:
            self.subtitle_lbl.configure(text="Select a document from the queue to edit metadata.")
            return

        self.subtitle_lbl.configure(text=f"Editing: {item.filename}")
        meta = item.metadata

        self._set_entry_text(self.title_entry, meta.get("title", ""))
        self._set_entry_text(self.author_entry, meta.get("author", ""))
        self._set_entry_text(self.publisher_entry, meta.get("publisher", ""))
        self.lang_combo.set(meta.get("language", "en-US"))
        self._set_entry_text(self.subject_entry, meta.get("subject", ""))
        self._set_entry_text(self.rights_entry, meta.get("rights", ""))
        
        cover_path = meta.get("cover_image", "")
        self._set_entry_text(self.cover_path_entry, cover_path)
        self._update_cover_preview(cover_path)

    def _set_entry_text(self, entry: ctk.CTkEntry, text: str):
        entry.delete(0, "end")
        entry.insert(0, text)

    def _browse_cover_image(self):
        file_path = filedialog.askopenfilename(
            title="Select EPUB Cover Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp"), ("All Files", "*.*")]
        )
        if file_path:
            self._set_entry_text(self.cover_path_entry, file_path)
            self._update_cover_preview(file_path)

    def _update_cover_preview(self, path: str):
        if path and os.path.isfile(path):
            try:
                pil_img = Image.open(path)
                pil_img.thumbnail((120, 100))
                self._cover_ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.cover_preview_lbl.configure(image=self._cover_ctk_img, text="")
                return
            except Exception as e:
                pass
        self.cover_preview_lbl.configure(image=None, text="[ No Cover Image Preview ]")

    def _apply_metadata(self, apply_to_all: bool):
        meta_dict = {
            "title": self.title_entry.get().strip(),
            "author": self.author_entry.get().strip(),
            "publisher": self.publisher_entry.get().strip(),
            "language": self.lang_combo.get().strip(),
            "subject": self.subject_entry.get().strip(),
            "rights": self.rights_entry.get().strip(),
            "cover_image": self.cover_path_entry.get().strip()
        }

        if self.current_item and not apply_to_all:
            self.current_item.metadata.update(meta_dict)

        self.on_metadata_changed(meta_dict, apply_to_all)
