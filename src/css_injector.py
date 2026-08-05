"""
Custom CSS Typography & EPUB Style Injector Engine.
Manages built-in CSS presets, custom user CSS injection, font overrides,
and generates Pandoc style options.
"""
import os
import glob
import logging
from typing import Dict, List, Optional

from src.config import STYLES_DIR

logger = logging.getLogger("CSSInjector")

class CSSInjectorEngine:
    """
    Manages custom CSS stylesheets for HTML5 & EPUB document transcoding.
    """

    def __init__(self):
        self.presets: Dict[str, str] = self._load_presets()

    def _load_presets(self) -> Dict[str, str]:
        """
        Discovers all bundled .css files in STYLES_DIR.
        """
        presets = {}
        if os.path.exists(STYLES_DIR):
            for path in glob.glob(os.path.join(STYLES_DIR, "*.css")):
                name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
                presets[name] = path
        return presets

    def get_presets(self) -> Dict[str, str]:
        self.presets = self._load_presets()
        return self.presets

    def get_preset_content(self, preset_name: str) -> str:
        path = self.presets.get(preset_name)
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read preset CSS '{preset_name}': {e}")
        return ""

    def generate_custom_css_file(
        self,
        base_css_content: str,
        output_temp_dir: str,
        font_family: Optional[str] = None,
        font_size_pt: Optional[int] = None,
        margin_em: Optional[float] = None
    ) -> str:
        """
        Creates a custom dynamic CSS file with font and margin overrides.
        """
        override_rules = []
        if font_family:
            override_rules.append(f"body {{ font-family: {font_family} !important; }}")
        if font_size_pt:
            override_rules.append(f"body {{ font-size: {font_size_pt}pt !important; }}")
        if margin_em is not None:
            override_rules.append(f"body {{ margin: {margin_em}em auto !important; }}")

        full_content = base_css_content
        if override_rules:
            full_content += "\n\n/* Dynamic Overrides */\n" + "\n".join(override_rules)

        os.makedirs(output_temp_dir, exist_ok=True)
        css_file_path = os.path.join(output_temp_dir, "injected_style.css")
        with open(css_file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return css_file_path

    def get_pandoc_css_args(self, css_file_path: Optional[str]) -> List[str]:
        """
        Generates Pandoc CLI arguments for CSS injection.
        """
        if css_file_path and os.path.isfile(css_file_path):
            return ["--css", css_file_path]
        return []
