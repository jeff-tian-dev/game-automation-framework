import json
import pyautogui
from pathlib import Path
from typing import Dict, Any, List
from app.utils.common import get_resource_path
from app.utils.logger import setup_logger

logger = setup_logger("Config")

class Config:
    """Singleton configuration manager."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.data: Dict[str, Any] = {}
        self.width: int = 0
        self.height: int = 0
        self.load_config()
        self._initialized = True

    def load_config(self) -> None:
        """Load configuration from data.json based on screen resolution."""
        try:
            config_path = get_resource_path("templates/data.json")
            with open(config_path, "r") as f:
                temp_data = json.load(f)

            self.width, self.height = pyautogui.size()
            
            # Resolution detection logic from original code
            if self.width == 1920 and self.height == 1080:
                logger.info(f"Resolution detected: 1920x1080")
                self.data = temp_data[1]
            else:
                logger.info(f"Resolution detected: {self.width}x{self.height} (Defaulting to 2560x1600 profile)")
                self.data = temp_data[0]
                
        except FileNotFoundError:
            logger.error("data.json not found in templates directory!")
            raise
        except json.JSONDecodeError:
            logger.error("data.json is invalid JSON!")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def get_point(self, key: str) -> List[int]:
        """Retrieve a coordinate point from config."""
        val = self.data.get(key)
        if not val:
            raise KeyError(f"Key '{key}' not found in configuration.")
        return val

    def reload(self):
        """Reload configuration from disk."""
        self.load_config()
