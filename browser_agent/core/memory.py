import json
import os
from ..utils.logger import setup_logger

logger = setup_logger("memory")

MEMORY_FILE = "user_data.json"

class MemoryManager:
    def __init__(self):
        self.file_path = MEMORY_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({"name": "", "email": "", "address": "", "notes": ""}, f, indent=4)

    def load(self) -> dict:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return {}

    def save(self, data: dict):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def update(self, key: str, value: str):
        data = self.load()
        data[key] = value
        self.save(data)

    def get_context_string(self) -> str:
        data = self.load()
        context = "USER PROFILE / MEMORY:\n"
        for k, v in data.items():
            if v: # Only show non-empty fields
                context += f"{k.title().replace('_', ' ')}: {v}\n"
        return context
