"""
Dublin Core Metadata Batch Editor & Frontmatter Builder.
Handles Dublin Core specification fields and translates them into
Pandoc CLI arguments, YAML frontmatter, or EPUB metadata blocks.
"""
import os
import yaml
import logging
from typing import Dict, Any, List

logger = logging.getLogger("DublinCore")

DUBLIN_CORE_SCHEMA = {
    "title": "Title",
    "author": "Creator / Author",
    "publisher": "Publisher",
    "language": "Language (RFC 5646)",
    "subject": "Subject / Keywords",
    "rights": "Rights / Copyright",
    "identifier": "Identifier (ISBN/URI)",
    "cover_image": "Cover Image File Path"
}

class DublinCoreManager:
    """
    Utilities for reading, editing, and formatting Dublin Core metadata.
    """

    @staticmethod
    def sanitize_metadata(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Cleans and normalizes metadata dictionary values.
        """
        clean = {}
        for key in DUBLIN_CORE_SCHEMA.keys():
            val = str(data.get(key, "")).strip()
            clean[key] = val
        if not clean["language"]:
            clean["language"] = "en-US"
        return clean

    @staticmethod
    def build_pandoc_args(metadata: Dict[str, Any]) -> List[str]:
        """
        Generates Pandoc command-line metadata arguments.
        Example: ['--metadata', 'title=My Book', '--metadata', 'author=John Doe']
        """
        args = []
        clean = DublinCoreManager.sanitize_metadata(metadata)

        if clean.get("title"):
            args.extend(["--metadata", f"title={clean['title']}"])
        if clean.get("author"):
            args.extend(["--metadata", f"author={clean['author']}"])
        if clean.get("publisher"):
            args.extend(["--metadata", f"publisher={clean['publisher']}"])
        if clean.get("language"):
            args.extend(["--metadata", f"lang={clean['language']}"])
            args.extend(["--metadata", f"language={clean['language']}"])
        if clean.get("subject"):
            args.extend(["--metadata", f"subject={clean['subject']}"])
        if clean.get("rights"):
            args.extend(["--metadata", f"rights={clean['rights']}"])

        # EPUB Cover Image argument
        cover_path = clean.get("cover_image", "")
        if cover_path and os.path.isfile(cover_path):
            args.extend(["--epub-cover-image", cover_path])

        return args

    @staticmethod
    def build_yaml_frontmatter(metadata: Dict[str, Any]) -> str:
        """
        Builds a YAML frontmatter block for Markdown or HTML document heads.
        """
        clean = DublinCoreManager.sanitize_metadata(metadata)
        frontmatter_data = {
            "title": clean.get("title", ""),
            "author": clean.get("author", ""),
            "publisher": clean.get("publisher", ""),
            "lang": clean.get("language", "en-US"),
            "subject": clean.get("subject", ""),
            "rights": clean.get("rights", "")
        }
        yaml_str = yaml.dump(frontmatter_data, sort_keys=False, default_flow_style=False)
        return f"---\n{yaml_str}---\n\n"

    @staticmethod
    def inject_frontmatter_to_text(text: str, metadata: Dict[str, Any]) -> str:
        """
        Prepends YAML frontmatter block to text if it doesn't already contain one.
        """
        frontmatter = DublinCoreManager.build_yaml_frontmatter(metadata)
        if text.startswith("---"):
            # Replace existing frontmatter if present
            end_idx = text.find("\n---", 3)
            if end_idx != -1:
                return frontmatter + text[end_idx + 4:].lstrip()
        return frontmatter + text
