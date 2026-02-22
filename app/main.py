import sys
from multiprocessing import freeze_support
from app.ui.gui import run_gui
from app.utils.logger import setup_logger

logger = setup_logger("Main")

def main():
    try:
        logger.info("Starting Application...")
        run_gui()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    freeze_support()
    main()
