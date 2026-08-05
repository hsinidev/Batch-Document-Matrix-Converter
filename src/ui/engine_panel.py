"""
5-Tier Pandoc Engine & Resolver Status UI Panel.
"""
import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Optional

from src.binary_resolver import PandocBinaryResolver
from src.ui.theme import UIStyle

class EngineStatusPanel(ctk.CTkFrame):
    """
    Inspector for Pandoc runtime executable resolution and engine settings.
    """

    def __init__(
        self,
        master,
        resolver: PandocBinaryResolver,
        on_resolver_updated: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color=UIStyle.BG_SECONDARY, corner_radius=10, **kwargs)
        self.resolver = resolver
        self.on_resolver_updated = on_resolver_updated
        self._build_ui()

    def _build_ui(self):
        title_lbl = ctk.CTkLabel(
            self,
            text="Embedded Pandoc Engine & 5-Tier Resolver",
            font=UIStyle.FONT_SUBHEADING,
            text_color=UIStyle.ACCENT_PRIMARY
        )
        title_lbl.pack(anchor="w", padx=15, pady=(15, 5))

        subtitle_lbl = ctk.CTkLabel(
            self,
            text="Monitors binary resolution tier, version validity, and offline execution capabilities.",
            font=UIStyle.FONT_CAPTION,
            text_color=UIStyle.TEXT_SECONDARY
        )
        subtitle_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        container = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Engine Status Badge Card
        status_card = ctk.CTkFrame(container, fg_color=UIStyle.BG_PRIMARY, corner_radius=6)
        status_card.pack(fill="x", padx=15, pady=15)

        self.status_icon_lbl = ctk.CTkLabel(status_card, text="⚙️ Engine Status:", font=UIStyle.FONT_BODY_BOLD, text_color=UIStyle.TEXT_PRIMARY)
        self.status_icon_lbl.pack(side="left", padx=15, pady=12)

        self.status_val_lbl = ctk.CTkLabel(
            status_card,
            text="Resolving...",
            font=UIStyle.FONT_BODY_BOLD,
            text_color=UIStyle.WARNING
        )
        self.status_val_lbl.pack(side="right", padx=15)

        # 2. Details Grid
        details_frame = ctk.CTkFrame(container, fg_color="transparent")
        details_frame.pack(fill="x", padx=15, pady=5)

        self.path_lbl = self._create_info_row(details_frame, "Binary Path:", "Not Found")
        self.version_lbl = self._create_info_row(details_frame, "Pandoc Version:", "Unknown")
        self.tier_lbl = self._create_info_row(details_frame, "Resolution Tier:", "None")
        self.details_lbl = self._create_info_row(details_frame, "Tier Strategy:", "Scanning...")

        # 3. Manual Override & Download Actions
        actions_frame = ctk.CTkFrame(container, fg_color=UIStyle.BG_PRIMARY, corner_radius=6)
        actions_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(actions_frame, text="Binary Override Actions:", font=UIStyle.FONT_BODY_BOLD, text_color=UIStyle.TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))

        btn_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        browse_btn = ctk.CTkButton(
            btn_row,
            text="📁 Select pandoc.exe",
            font=UIStyle.FONT_BODY,
            fg_color=UIStyle.SURFACE_CARD,
            border_color=UIStyle.ACCENT_PRIMARY,
            border_width=1,
            hover_color=UIStyle.ACCENT_PRIMARY,
            command=self._browse_manual_binary
        )
        browse_btn.pack(side="left", expand=True, fill="x", padx=5)

        download_btn = ctk.CTkButton(
            btn_row,
            text="⬇️ Auto-Download Pandoc",
            font=UIStyle.FONT_BODY,
            fg_color=UIStyle.ACCENT_SECONDARY,
            hover_color=UIStyle.ACCENT_HOVER,
            command=self._download_pandoc
        )
        download_btn.pack(side="right", expand=True, fill="x", padx=5)

        self.refresh_info()

    def _create_info_row(self, parent, label_text: str, default_val: str) -> ctk.CTkLabel:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=label_text, font=UIStyle.FONT_BODY_BOLD, text_color=UIStyle.TEXT_SECONDARY, width=120, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=default_val, font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_PRIMARY, anchor="w")
        val_lbl.pack(side="left", expand=True, fill="x")
        return val_lbl

    def refresh_info(self):
        info = self.resolver.get_info()
        if info["is_valid"]:
            self.status_val_lbl.configure(text=f"READY (v{info['version']})", text_color=UIStyle.SUCCESS)
            self.path_lbl.configure(text=info["path"])
            self.version_lbl.configure(text=info["version"])
            self.tier_lbl.configure(text=f"Tier {info['tier']}")
            self.details_lbl.configure(text=info["details"])
        else:
            self.status_val_lbl.configure(text="UNRESOLVED", text_color=UIStyle.DANGER)
            self.path_lbl.configure(text="Pandoc binary not found")
            self.version_lbl.configure(text="N/A")
            self.tier_lbl.configure(text="Tier 0")
            self.details_lbl.configure(text=info["details"])

    def _browse_manual_binary(self):
        file_path = filedialog.askopenfilename(
            title="Locate pandoc.exe Executable",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.resolver.manual_path = file_path
            self.resolver.resolve()
            self.refresh_info()
            self.on_resolver_updated()

    def _download_pandoc(self):
        self.status_val_lbl.configure(text="DOWNLOADING...", text_color=UIStyle.WARNING)
        success, msg = self.resolver.download_pandoc_binary()
        self.refresh_info()
        self.on_resolver_updated()
