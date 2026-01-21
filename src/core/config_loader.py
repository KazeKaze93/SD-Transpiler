from PyQt6.QtCore import QSettings

from src.core.security import security


class ConfigManager:
    def __init__(self):
        self.settings = QSettings("SD-Transpiler", "General")

    def get_api_key(self) -> str:
        return security.get_api_key()

    def save_api_key(self, key: str):
        security.save_api_key(key)

# Singleton
config_manager = ConfigManager()