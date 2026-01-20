import os
import sys

from PyQt5.QtWidgets import QApplication

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


def main():
    app = QApplication(sys.argv)

    try:
        from qt_material import apply_stylesheet
        from src.ui.interface import TranspilerUI
    except ImportError as e:
        print(f"Критическая ошибка: {e}")
        return

    extra = {
        'secondary_color': '#3b82f6',
        'secondary_light_color': '#60a5fa',
    }

    apply_stylesheet(app, theme='dark_blue.xml', extra=extra)

    window = TranspilerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()