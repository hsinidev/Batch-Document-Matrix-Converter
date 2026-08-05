"""
Config definitions, theme palette, typography tokens, and conversion matrix specifications
for Batch Document Matrix Converter.
"""
import os
import sys

# Application Metadata
APP_NAME = "Batch Document Matrix Converter"
APP_VERSION = "1.0.0-PROD"
APP_AUTHOR = "Document Engineering Specialist"

# Color Palette: Steel Indigo & Electric Violet
THEME_COLORS = {
    "background_primary": "#0D0E15",
    "background_secondary": "#151722",
    "surface_card": "#1A1C26",
    "accent_primary": "#8B5CF6",     # Electric Violet
    "accent_secondary": "#06B6D4",   # Cyan
    "accent_hover": "#7C3AED",       # Deep Purple Hover
    "text_primary": "#F3F4F6",       # Light Grey
    "text_secondary": "#9CA3AF",     # Mid Grey
    "danger_red": "#EF4444",
    "warning_amber": "#F59E0B",
    "success_emerald": "#10B981",
    "border_color": "#292D3E"
}

# Typography Standards
TYPOGRAPHY = {
    "font_family": "Segoe UI",
    "mono_family": "Cascadia Code",
    "heading_size": 18,
    "subheading_size": 14,
    "body_size": 12,
    "caption_size": 10
}

# Universal Transcoding Matrix Supported Formats
SUPPORTED_FORMATS = {
    "txt": {"name": "Plain Text", "ext": ".txt", "pandoc": "plain", "mime": "text/plain"},
    "docx": {"name": "Microsoft Word Document", "ext": ".docx", "pandoc": "docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "epub": {"name": "EPUB Ebook", "ext": ".epub", "pandoc": "epub", "mime": "application/epub+zip"},
    "html": {"name": "HTML5 Web Document", "ext": ".html", "pandoc": "html5", "mime": "text/html"},
    "md": {"name": "Markdown (GFM)", "ext": ".md", "pandoc": "gfm", "mime": "text/markdown"},
    "rtf": {"name": "Rich Text Format", "ext": ".rtf", "pandoc": "rtf", "mime": "application/rtf"}
}

# File Extensions Set for Fast Filtering
VALID_EXTENSIONS = {f".{ext}" for ext in SUPPORTED_FORMATS.keys()}

# Default Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
STYLES_DIR = os.path.join(BASE_DIR, "styles")
BIN_DIR = os.path.join(BASE_DIR, "bin", "pandoc")
TEMP_DIR = os.path.join(BASE_DIR, ".temp_conversion")

# Ensure critical directories exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(STYLES_DIR, exist_ok=True)
os.makedirs(BIN_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
