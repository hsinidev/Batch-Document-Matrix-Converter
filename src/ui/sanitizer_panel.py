"""
BeautifulSoup4 DOM Sanitizer & Pandoc Flag Settings Panel.
"""
import customtkinter as ctk
from typing import Dict, Any, Callable

from src.ui.theme import UIStyle

class SanitizerOptionsPanel(ctk.CTkFrame):
    """
    DOM Tree Cleanup & Pandoc Export Options Panel.
    """

    def __init__(
        self,
        master,
        on_options_changed: Callable[[Dict[str, Any]], None],
        **kwargs
    ):
        super().__init__(master, fg_color=UIStyle.BG_SECONDARY, corner_radius=10, **kwargs)
        self.on_options_changed = on_options_changed
        self._build_ui()

    def _build_ui(self):
        title_lbl = ctk.CTkLabel(
            self,
            text="BeautifulSoup4 DOM Sanitizer & Export Flags",
            font=UIStyle.FONT_SUBHEADING,
            text_color=UIStyle.ACCENT_PRIMARY
        )
        title_lbl.pack(anchor="w", padx=15, pady=(15, 5))

        subtitle_lbl = ctk.CTkLabel(
            self,
            text="Configure automated DOM tree sanitization, media path resolution, and Pandoc flags.",
            font=UIStyle.FONT_CAPTION,
            text_color=UIStyle.TEXT_SECONDARY
        )
        subtitle_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        container = ctk.CTkScrollableFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Master DOM Sanitizer Switch
        self.dom_switch = ctk.CTkSwitch(
            container,
            text="Enable BeautifulSoup4 Pre-Conversion DOM Cleanser",
            font=UIStyle.FONT_BODY_BOLD,
            text_color=UIStyle.TEXT_PRIMARY,
            progress_color=UIStyle.ACCENT_PRIMARY,
            command=self._notify
        )
        self.dom_switch.select()
        self.dom_switch.pack(anchor="w", padx=15, pady=10)

        # Sanitizer options group box
        sub_group = ctk.CTkFrame(container, fg_color=UIStyle.BG_PRIMARY, corner_radius=6)
        sub_group.pack(fill="x", padx=15, pady=5)

        self.fix_img_chk = ctk.CTkCheckBox(
            sub_group,
            text="Resolve & Embed Relative Image/Media Paths",
            font=UIStyle.FONT_BODY,
            command=self._notify
        )
        self.fix_img_chk.select()
        self.fix_img_chk.pack(anchor="w", padx=15, pady=8)

        self.strip_style_chk = ctk.CTkCheckBox(
            sub_group,
            text="Strip Redundant Inline Tag Styles (style='...')",
            font=UIStyle.FONT_BODY,
            command=self._notify
        )
        self.strip_style_chk.pack(anchor="w", padx=15, pady=8)

        self.remove_empty_chk = ctk.CTkCheckBox(
            sub_group,
            text="Purge Empty HTML Elements (<p></p>, <span></span>)",
            font=UIStyle.FONT_BODY,
            command=self._notify
        )
        self.remove_empty_chk.select()
        self.remove_empty_chk.pack(anchor="w", padx=15, pady=8)

        self.norm_headings_chk = ctk.CTkCheckBox(
            sub_group,
            text="Normalize Heading Anchors & Generate Unique IDs",
            font=UIStyle.FONT_BODY,
            command=self._notify
        )
        self.norm_headings_chk.select()
        self.norm_headings_chk.pack(anchor="w", padx=15, pady=8)

        # 2. Pandoc Flags Section
        ctk.CTkLabel(
            container,
            text="Pandoc Transcoding Flags:",
            font=UIStyle.FONT_BODY_BOLD,
            text_color=UIStyle.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 5))

        p_group = ctk.CTkFrame(container, fg_color=UIStyle.BG_PRIMARY, corner_radius=6)
        p_group.pack(fill="x", padx=15, pady=5)

        self.toc_chk = ctk.CTkCheckBox(
            p_group,
            text="Generate Table of Contents (--toc)",
            font=UIStyle.FONT_BODY,
            command=self._notify
        )
        self.toc_chk.select()
        self.toc_chk.pack(anchor="w", padx=15, pady=8)

        self.standalone_chk = ctk.CTkCheckBox(
            p_group,
            text="Export Standalone Complete Document (--standalone)",
            font=UIStyle.FONT_BODY,
            command=self._notify
        )
        self.standalone_chk.select()
        self.standalone_chk.pack(anchor="w", padx=15, pady=8)

    def _notify(self):
        self.on_options_changed(self.get_options())

    def get_options(self) -> Dict[str, Any]:
        return {
            "enable_dom_sanitizer": bool(self.dom_switch.get()),
            "sanitizer_options": {
                "fix_image_paths": bool(self.fix_img_chk.get()),
                "strip_inline_styles": bool(self.strip_style_chk.get()),
                "remove_empty_tags": bool(self.remove_empty_chk.get()),
                "normalize_headings": bool(self.norm_headings_chk.get())
            },
            "generate_toc": bool(self.toc_chk.get()),
            "standalone": bool(self.standalone_chk.get())
        }
