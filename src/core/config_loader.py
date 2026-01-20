from PyQt5.QtCore import QSettings

class ConfigManager:
    def __init__(self):
        self.settings = QSettings("KazeProjects", "SD-Transpiler")

    def get_api_key(self) -> str:
        return self.settings.value("gemini_api_key", "")

    def save_api_key(self, key: str):
        self.settings.setValue("gemini_api_key", key.strip())


# Singleton
config_manager = ConfigManager()