import json
import os
from ..utils.logger import setup_logger

logger = setup_logger("settings")

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "provider": "lm_studio",  # or "gemini"
    "lm_studio_url": "http://localhost:1234/v1",
    "lm_studio_model": "qwen/qwen3-vl-8b",
    "gemini_api_key": "",
    "gemini_model": "gemini-1.5-flash-latest"
}

class SettingsManager:
    def __init__(self):
        self.file_path = SETTINGS_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            self.save(DEFAULT_SETTINGS)

    def load(self) -> dict:
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_SETTINGS, **data}
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return DEFAULT_SETTINGS

    def save(self, data: dict):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
