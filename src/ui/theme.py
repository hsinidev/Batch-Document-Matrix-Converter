"""
CustomTkinter Theme & Styling Specifications for Steel Indigo & Electric Violet.
"""
import customtkinter as ctk
from src.config import THEME_COLORS, TYPOGRAPHY

def setup_app_theme():
    """
    Initializes CustomTkinter dark mode settings.
    """
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

class UIStyle:
    BG_PRIMARY = THEME_COLORS["background_primary"]
    BG_SECONDARY = THEME_COLORS["background_secondary"]
    SURFACE_CARD = THEME_COLORS["surface_card"]
    ACCENT_PRIMARY = THEME_COLORS["accent_primary"]
    ACCENT_SECONDARY = THEME_COLORS["accent_secondary"]
    ACCENT_HOVER = THEME_COLORS["accent_hover"]
    TEXT_PRIMARY = THEME_COLORS["text_primary"]
    TEXT_SECONDARY = THEME_COLORS["text_secondary"]
    DANGER = THEME_COLORS["danger_red"]
    WARNING = THEME_COLORS["warning_amber"]
    SUCCESS = THEME_COLORS["success_emerald"]
    BORDER = THEME_COLORS["border_color"]

    FONT_HEADING = (TYPOGRAPHY["font_family"], TYPOGRAPHY["heading_size"], "bold")
    FONT_SUBHEADING = (TYPOGRAPHY["font_family"], TYPOGRAPHY["subheading_size"], "bold")
    FONT_BODY = (TYPOGRAPHY["font_family"], TYPOGRAPHY["body_size"])
    FONT_BODY_BOLD = (TYPOGRAPHY["font_family"], TYPOGRAPHY["body_size"], "bold")
    FONT_CAPTION = (TYPOGRAPHY["font_family"], TYPOGRAPHY["caption_size"])
    FONT_MONO = (TYPOGRAPHY["mono_family"], TYPOGRAPHY["body_size"])
