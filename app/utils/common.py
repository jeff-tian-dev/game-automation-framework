import os
import sys
from pathlib import Path
from typing import Tuple, Optional

# Type aliases
Point = Tuple[int, int]
Rect = Tuple[int, int, int, int]  # x, y, w, h

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS) # type: ignore
    except Exception:
        base_path = Path(os.path.abspath("."))

    return base_path / relative_path

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
