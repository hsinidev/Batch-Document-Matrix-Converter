"""
BeautifulSoup4 HTML/EPUB DOM Sanitizer Engine.
Pre-parses DOM structures to clean redundant inline styles, resolve relative
media paths, purge malformed tags, and optimize layout prior to Pandoc compilation.
"""
import os
import re
import logging
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("DOMSanitizer")

class DOMSanitizer:
    """
    Cleans and normalizes HTML / Markdown AST trees prior to document conversion.
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = options or {
            "strip_inline_styles": False,
            "fix_image_paths": True,
            "remove_empty_tags": True,
            "normalize_headings": True
        }

    def sanitize_html(self, html_content: str, base_dir: str) -> Tuple[str, Dict[str, int]]:
        """
        Sanitizes HTML content and resolves relative file assets.
        Returns: (sanitized_html_str, statistics_dict)
        """
        stats = {
            "images_resolved": 0,
            "styles_stripped": 0,
            "empty_tags_removed": 0
        }

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # 1. Resolve relative image / media paths
            if self.options.get("fix_image_paths"):
                for img in soup.find_all(["img", "source", "embed"]):
                    src = img.get("src") or img.get("href")
                    if src and not src.startswith(("http://", "https://", "data:", "file://")):
                        abs_path = os.path.abspath(os.path.join(base_dir, src))
                        if os.path.isfile(abs_path):
                            img["src"] = abs_path.replace("\\", "/")
                            stats["images_resolved"] += 1

            # 2. Strip redundant inline style attributes if requested
            if self.options.get("strip_inline_styles"):
                for tag in soup.find_all(True):
                    if tag.has_attr("style"):
                        del tag["style"]
                        stats["styles_stripped"] += 1

            # 3. Purge empty structural tags
            if self.options.get("remove_empty_tags"):
                for tag in soup.find_all(["p", "span", "div", "b", "i", "u"]):
                    if not tag.contents or (not tag.get_text(strip=True) and not tag.find_all(["img", "svg", "iframe", "br"])):
                        tag.decompose()
                        stats["empty_tags_removed"] += 1

            # 4. Normalize heading hierarchy if requested
            if self.options.get("normalize_headings"):
                headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                for h in headings:
                    # Ensure headings have unique ID attributes for TOC linking
                    if not h.get("id"):
                        text_slug = re.sub(r"[^\w\s-]", "", h.get_text().lower()).strip()
                        h["id"] = re.sub(r"[-\s]+", "-", text_slug) or f"heading-{id(h)}"

            return str(soup), stats

        except Exception as e:
            logger.error(f"DOM Sanitization error: {e}")
            return html_content, stats
