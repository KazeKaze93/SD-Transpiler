import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtCore import Qt
import os

# 1. Сначала железно фиксим пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


def main():
    # 2. Создаем приложение ДО ЛЮБОГО импорта qt_material
    app = QApplication(sys.argv)

    # 3. Импортируем стили и UI только когда QApplication уже в памяти
    # Это гарантирует, что qt_material увидит правильный биндинг
    try:
        from qt_material import apply_stylesheet
        from src.ui.interface import TranspilerUI
    except ImportError as e:
        print(f"Критическая ошибка: {e}")
        return

    # 4. Выжигаем желтый цвет через extra
    extra = {
        'secondary_color': '#3b82f6',
        'secondary_light_color': '#60a5fa',
    }

    # Применяем тему строго здесь
    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)

    window = TranspilerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()