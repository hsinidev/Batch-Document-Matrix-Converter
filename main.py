"""
Application Entry Point for Batch Document Matrix Converter.
Initializes TkinterDnD2 drag & drop context, loads Steel Indigo & Electric Violet theme,
and launches CustomTkinter main loop.
"""
import sys
import os
import logging

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Main")

# Attempt native TkinterDnD import
try:
    from tkinterdnd2 import TkinterDnD
    HAS_TKINTERDND = True
except Exception as e:
    logger.warning(f"TkinterDnD2 native wrapper unavailable: {e}")
    HAS_TKINTERDND = False

from src.ui.main_window import MainWindow

def main():
    logger.info("Starting Batch Document Matrix Converter...")
    
    # Initialize App Window
    app = MainWindow()
    
    # Enable native Drag and Drop if TkinterDnD wrapper is active
    if HAS_TKINTERDND and hasattr(app, "drop_target_register"):
        try:
            app.drop_target_register("DND_Files")
        except Exception as e:
            logger.debug(f"Root DND registration note: {e}")

    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
