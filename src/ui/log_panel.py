"""
Real-time Telemetry & Execution Log Console UI Panel.
"""
import time
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional

from src.ui.theme import UIStyle

class LogConsolePanel(ctk.CTkFrame):
    """
    Scrollable colored log terminal for streaming conversion telemetry events.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=UIStyle.BG_SECONDARY, corner_radius=10, **kwargs)
        self._build_ui()

    def _build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8, height=35)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Execution Log & Telemetry",
            font=UIStyle.FONT_SUBHEADING,
            text_color=UIStyle.ACCENT_PRIMARY
        )
        title_lbl.pack(side="left", padx=12, pady=5)

        self.autoscroll_chk = ctk.CTkCheckBox(
            header_frame,
            text="Auto-scroll",
            font=UIStyle.FONT_CAPTION,
            command=None
        )
        self.autoscroll_chk.select()
        self.autoscroll_chk.pack(side="right", padx=10)

        clear_btn = ctk.CTkButton(
            header_frame,
            text="Clear",
            width=50,
            height=24,
            fg_color="transparent",
            text_color=UIStyle.TEXT_SECONDARY,
            hover_color=UIStyle.BG_PRIMARY,
            command=self.clear_log
        )
        clear_btn.pack(side="right", padx=2)

        export_btn = ctk.CTkButton(
            header_frame,
            text="Export",
            width=55,
            height=24,
            fg_color=UIStyle.BG_PRIMARY,
            text_color=UIStyle.TEXT_PRIMARY,
            hover_color=UIStyle.ACCENT_PRIMARY,
            command=self.export_log
        )
        export_btn.pack(side="right", padx=5)

        # Log Textbox
        self.textbox = ctk.CTkTextbox(
            self,
            font=UIStyle.FONT_MONO,
            fg_color=UIStyle.BG_PRIMARY,
            text_color=UIStyle.TEXT_PRIMARY,
            border_color=UIStyle.BORDER,
            border_width=1,
            wrap="none"
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def log(self, level: str, message: str):
        timestamp = time.strftime("[%H:%M:%S]")
        prefix = f"{timestamp} [{level.upper():<7}] "
        line = f"{prefix} {message}\n"

        self.textbox.insert("end", line)
        if self.autoscroll_chk.get():
            self.textbox.see("end")

    def clear_log(self):
        self.textbox.delete("1.0", "end")

    def export_log(self):
        content = self.textbox.get("1.0", "end-1c")
        file_path = filedialog.asksaveasfilename(
            title="Export Execution Log",
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                pass
