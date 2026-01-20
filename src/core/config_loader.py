import os
from typing import Optional
from dotenv import load_dotenv, set_key


class ConfigManager:
    def __init__(self):
        # Путь к корню проекта (выходим из src/core/)
        self.base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.env_path = os.path.join(self.base_path, '.env')
        load_dotenv(self.env_path)

    def get_api_key(self) -> Optional[str]:
        """Loads API Key from .env"""
        return os.getenv("GEMINI_API_KEY")

    def save_api_key(self, key: str):
        """Saves API Key to .env"""
        # Создаем файл, если его нет
        if not os.path.exists(self.env_path):
            with open(self.env_path, 'w') as f:
                f.write("")

        set_key(self.env_path, "GEMINI_API_KEY", key.strip())
        # Перезагружаем переменные окружения после записи
        load_dotenv(self.env_path, override=True)


config_manager = ConfigManager()