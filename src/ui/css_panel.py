"""
Custom CSS Typography & Style Injector UI Panel.
"""
import customtkinter as ctk
from typing import Dict, Any, Callable

from src.css_injector import CSSInjectorEngine
from src.ui.theme import UIStyle

class CSSInjectorPanel(ctk.CTkFrame):
    """
    CSS Preset Selector & Live Typography Stylesheet Editor.
    """

    def __init__(
        self,
        master,
        css_engine: CSSInjectorEngine,
        on_css_options_changed: Callable[[Dict[str, Any]], None],
        **kwargs
    ):
        super().__init__(master, fg_color=UIStyle.BG_SECONDARY, corner_radius=10, **kwargs)
        self.css_engine = css_engine
        self.on_css_options_changed = on_css_options_changed
        
        self.presets = self.css_engine.get_presets()
        self._build_ui()

    def _build_ui(self):
        title_lbl = ctk.CTkLabel(
            self,
            text="CSS Typography & EPUB Style Injector",
            font=UIStyle.FONT_SUBHEADING,
            text_color=UIStyle.ACCENT_PRIMARY
        )
        title_lbl.pack(anchor="w", padx=15, pady=(15, 5))

        subtitle_lbl = ctk.CTkLabel(
            self,
            text="Inject custom stylesheets and dynamic typography overrides into EPUB and HTML5 exports.",
            font=UIStyle.FONT_CAPTION,
            text_color=UIStyle.TEXT_SECONDARY
        )
        subtitle_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Preset Selector Bar
        preset_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        preset_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(preset_frame, text="CSS Preset Theme:", font=UIStyle.FONT_BODY_BOLD, text_color=UIStyle.TEXT_PRIMARY).pack(side="left", padx=10, pady=8)

        preset_names = list(self.presets.keys()) if self.presets else ["Default Clean"]
        self.preset_combo = ctk.CTkComboBox(
            preset_frame,
            values=preset_names,
            command=self._on_preset_selected,
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER,
            button_color=UIStyle.ACCENT_PRIMARY
        )
        self.preset_combo.pack(side="left", expand=True, fill="x", padx=10, pady=8)

        # Dynamic Typography Sliders Frame
        overrides_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        overrides_frame.pack(fill="x", padx=10, pady=5)

        # 1. Font Family Override
        font_row = ctk.CTkFrame(overrides_frame, fg_color="transparent")
        font_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(font_row, text="Font Family:", font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_PRIMARY, width=90, anchor="w").pack(side="left")
        self.font_entry = ctk.CTkEntry(
            font_row,
            placeholder_text="e.g. 'Segoe UI', Inter, Georgia, sans-serif",
            fg_color=UIStyle.BG_PRIMARY,
            border_color=UIStyle.BORDER
        )
        self.font_entry.pack(side="left", expand=True, fill="x", padx=5)

        # 2. Font Size Slider (pt)
        size_row = ctk.CTkFrame(overrides_frame, fg_color="transparent")
        size_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(size_row, text="Base Font Size:", font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_PRIMARY, width=90, anchor="w").pack(side="left")
        self.size_slider = ctk.CTkSlider(
            size_row,
            from_=8,
            to=24,
            number_of_steps=16,
            command=self._on_slider_changed,
            button_color=UIStyle.ACCENT_PRIMARY
        )
        self.size_slider.set(11)
        self.size_slider.pack(side="left", expand=True, fill="x", padx=5)
        self.size_val_lbl = ctk.CTkLabel(size_row, text="11 pt", font=UIStyle.FONT_CAPTION, text_color=UIStyle.ACCENT_SECONDARY, width=45)
        self.size_val_lbl.pack(side="right")

        # 3. Margin Slider (em)
        margin_row = ctk.CTkFrame(overrides_frame, fg_color="transparent")
        margin_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(margin_row, text="Page Margin:", font=UIStyle.FONT_BODY, text_color=UIStyle.TEXT_PRIMARY, width=90, anchor="w").pack(side="left")
        self.margin_slider = ctk.CTkSlider(
            margin_row,
            from_=0.5,
            to=5.0,
            number_of_steps=45,
            command=self._on_slider_changed,
            button_color=UIStyle.ACCENT_PRIMARY
        )
        self.margin_slider.set(2.0)
        self.margin_slider.pack(side="left", expand=True, fill="x", padx=5)
        self.margin_val_lbl = ctk.CTkLabel(margin_row, text="2.0 em", font=UIStyle.FONT_CAPTION, text_color=UIStyle.ACCENT_SECONDARY, width=45)
        self.margin_val_lbl.pack(side="right")

        # Live CSS Editor Container
        editor_frame = ctk.CTkFrame(self, fg_color=UIStyle.SURFACE_CARD, corner_radius=8)
        editor_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(editor_frame, text="Stylesheet Code Inspector / Editor:", font=UIStyle.FONT_BODY_BOLD, text_color=UIStyle.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(8, 2))

        self.css_textbox = ctk.CTkTextbox(
            editor_frame,
            font=UIStyle.FONT_MONO,
            fg_color=UIStyle.BG_PRIMARY,
            text_color=UIStyle.TEXT_PRIMARY,
            border_color=UIStyle.BORDER,
            border_width=1
        )
        self.css_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Select first preset by default
        if preset_names:
            self._on_preset_selected(preset_names[0])

    def _on_preset_selected(self, preset_name: str):
        content = self.css_engine.get_preset_content(preset_name)
        self.css_textbox.delete("1.0", "end")
        self.css_textbox.insert("1.0", content)
        self._notify_changes()

    def _on_slider_changed(self, _val):
        size_pt = int(self.size_slider.get())
        margin_em = round(self.margin_slider.get(), 1)
        self.size_val_lbl.configure(text=f"{size_pt} pt")
        self.margin_val_lbl.configure(text=f"{margin_em} em")
        self._notify_changes()

    def _notify_changes(self):
        font_fam = self.font_entry.get().strip() or None
        options = {
            "css_preset": self.preset_combo.get(),
            "custom_css_text": self.css_textbox.get("1.0", "end-1c"),
            "override_font_family": font_fam,
            "override_font_size": int(self.size_slider.get()),
            "override_margin": round(self.margin_slider.get(), 1)
        }
        self.on_css_options_changed(options)

    def get_options(self) -> Dict[str, Any]:
        font_fam = self.font_entry.get().strip() or None
        return {
            "css_preset": self.preset_combo.get(),
            "custom_css_text": self.css_textbox.get("1.0", "end-1c"),
            "override_font_family": font_fam,
            "override_font_size": int(self.size_slider.get()),
            "override_margin": round(self.margin_slider.get(), 1)
        }
