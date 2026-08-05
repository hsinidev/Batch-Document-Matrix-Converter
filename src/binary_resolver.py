"""
5-Tier Embedded Pandoc Binary Resolver Engine.
Dynamically resolves pandoc.exe path across frozen PyInstaller bundles,
application directory, default Windows install locations, system PATH, or user override.
"""
import os
import sys
import shutil
import subprocess
import logging
import pypandoc
from typing import Tuple, Optional, Dict, Any

from src.config import BASE_DIR, BIN_DIR

logger = logging.getLogger("BinaryResolver")

class PandocBinaryResolver:
    """
    Resolves Pandoc binary location using a robust 5-tier strategy.
    """

    def __init__(self, manual_path: Optional[str] = None):
        self.manual_path = manual_path
        self._cached_path: Optional[str] = None
        self._cached_version: Optional[str] = None
        self._resolution_tier: Optional[int] = None
        self._resolution_details: str = ""

    def resolve(self) -> Tuple[Optional[str], Optional[str], int, str]:
        """
        Executes resolution strategy.
        Returns: (pandoc_path, pandoc_version, tier_index, tier_description)
        """
        # Tier 0: User manual override
        if self.manual_path and os.path.isfile(self.manual_path):
            ver = self._verify_binary(self.manual_path)
            if ver:
                self._update_cache(self.manual_path, ver, 5, f"Tier 5: User Manual Override ({self.manual_path})")
                return self._cached_path, self._cached_version, 5, self._resolution_details

        # Tier 1: sys._MEIPASS (PyInstaller frozen bundle)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            meipass_pandoc = os.path.join(sys._MEIPASS, "bin", "pandoc", "pandoc.exe")
            if os.path.isfile(meipass_pandoc):
                ver = self._verify_binary(meipass_pandoc)
                if ver:
                    self._update_cache(meipass_pandoc, ver, 1, "Tier 1: PyInstaller Bundled Binary (sys._MEIPASS)")
                    return self._cached_path, self._cached_version, 1, self._resolution_details

        # Tier 2: Application root directory / bin / pandoc / pandoc.exe
        local_bin_pandoc = os.path.join(BIN_DIR, "pandoc.exe")
        if os.path.isfile(local_bin_pandoc):
            ver = self._verify_binary(local_bin_pandoc)
            if ver:
                self._update_cache(local_bin_pandoc, ver, 2, f"Tier 2: Local App Binary ({local_bin_pandoc})")
                return self._cached_path, self._cached_version, 2, self._resolution_details

        # Tier 3: Local AppData / Program Files Pandoc default paths
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_appdata = os.environ.get("LOCALAPPDATA", "")

        common_paths = [
            os.path.join(program_files, "Pandoc", "pandoc.exe"),
            os.path.join(program_files_x86, "Pandoc", "pandoc.exe"),
            os.path.join(local_appdata, "Pandoc", "pandoc.exe"),
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "Pandoc", "pandoc.exe")
        ]

        for path in common_paths:
            if os.path.isfile(path):
                ver = self._verify_binary(path)
                if ver:
                    self._update_cache(path, ver, 3, f"Tier 3: Windows Standard Path ({path})")
                    return self._cached_path, self._cached_version, 3, self._resolution_details

        # Tier 4: System environment PATH (shutil.which)
        path_pandoc = shutil.which("pandoc")
        if path_pandoc and os.path.isfile(path_pandoc):
            ver = self._verify_binary(path_pandoc)
            if ver:
                self._update_cache(path_pandoc, ver, 4, f"Tier 4: System PATH ({path_pandoc})")
                return self._cached_path, self._cached_version, 4, self._resolution_details

        # Tier 5: Fallback to pypandoc download location if present
        try:
            download_dir = pypandoc.get_pandoc_path()
            if download_dir and os.path.isfile(download_dir):
                ver = self._verify_binary(download_dir)
                if ver:
                    self._update_cache(download_dir, ver, 5, f"Tier 5: pypandoc Managed Binary ({download_dir})")
                    return self._cached_path, self._cached_version, 5, self._resolution_details
        except Exception as e:
            logger.debug(f"pypandoc.get_pandoc_path() check failed: {e}")

        # Unresolved
        self._update_cache(None, None, 0, "Unresolved: Pandoc binary not found")
        return None, None, 0, self._resolution_details

    def download_pandoc_binary(self) -> Tuple[bool, str]:
        """
        Attempts to automatically download Pandoc v3+ using pypandoc.
        Target directory is set to BIN_DIR or default pypandoc location.
        """
        try:
            pypandoc.download_pandoc(targetfolder=BIN_DIR, download_folder=BIN_DIR)
            path, ver, tier, desc = self.resolve()
            if path:
                return True, f"Successfully downloaded Pandoc v{ver} to {path}"
            return False, "Download completed but binary verification failed."
        except Exception as e:
            logger.error(f"Download Pandoc failed: {e}")
            return False, f"Failed to download Pandoc binary: {str(e)}"

    def _verify_binary(self, binary_path: str) -> Optional[str]:
        """
        Executes binary --version to ensure it is executable and returns version string.
        """
        try:
            result = subprocess.run(
                [binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else ""
                # e.g. "pandoc 3.1.2" -> "3.1.2"
                parts = first_line.split()
                if len(parts) >= 2:
                    return parts[1]
                return first_line
        except Exception as e:
            logger.warning(f"Failed to execute pandoc at {binary_path}: {e}")
        return None

    def _update_cache(self, path: Optional[str], version: Optional[str], tier: int, details: str):
        self._cached_path = path
        self._cached_version = version
        self._resolution_tier = tier
        self._resolution_details = details
        if path:
            # Set environment variable so pypandoc knows which binary to use
            os.environ["PYPANDOC_PANDOC"] = path

    def get_info(self) -> Dict[str, Any]:
        path, version, tier, details = self.resolve()
        return {
            "path": path,
            "version": version,
            "tier": tier,
            "details": details,
            "is_valid": path is not None
        }
