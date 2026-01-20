import os
import sys

from PyQt5.QtWidgets import QApplication


def main():
    if getattr(sys, 'frozen', False):
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    app = QApplication(sys.argv)

    try:
        from qt_material import apply_stylesheet
        from src.ui.interface import TranspilerUI
    except ImportError as e:
        print(f"CRITICAL IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
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