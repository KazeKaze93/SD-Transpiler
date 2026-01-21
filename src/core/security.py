import base64

import win32crypt
from PyQt6.QtCore import QSettings


class SecurityManager:
    def __init__(self):
        self.settings = QSettings("SD-Transpiler", "Auth")

    def encrypt_data(self, plain_text: str) -> str:
        """
        Шифрует строку через Windows DPAPI и возвращает base64.
        """
        if not plain_text:
            return ""
        try:
            encrypted_bytes = win32crypt.CryptProtectData(
                plain_text.encode('utf-8'), None, None, None, None, 0
            )
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            print(f"CRITICAL: Encryption failed: {e}")
            return ""

    def decrypt_data(self, cipher_text: str) -> str:
        """
        Декодирует base64 и расшифровывает через Windows DPAPI.
        """
        if not cipher_text:
            return ""
        try:
            encrypted_bytes = base64.b64decode(cipher_text)
            _, plain_text = win32crypt.CryptUnprotectData(
                encrypted_bytes, None, None, None, 0
            )
            return plain_text.decode('utf-8')
        except Exception as e:
            print(f"CRITICAL: Decryption failed: {e}")
            return ""

    def get_api_key(self) -> str:
        cipher = self.settings.value("encrypted_key", "")
        return self.decrypt_data(str(cipher)) if cipher else ""

    def save_api_key(self, key: str):
        if not key or not key.strip():
            return
        cipher = self.encrypt_data(key.strip())
        self.settings.setValue("encrypted_key", cipher)


# Singleton
security = SecurityManager()
