import os
import sys

from PyQt6.QtWidgets import QApplication

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("SD-Transpiler")
    app.setOrganizationName("KazeKaze93")

    try:
        from qt_material import apply_stylesheet
        from src.ui.interface import TranspilerUI

        extra = {
            'density_scale': '-1',
            'font_family': 'Segoe UI',
        }
        apply_stylesheet(app, theme='dark_blue.xml', extra=extra)

        window = TranspilerUI()
        window.show()

        sys.exit(app.exec())

    except ImportError as e:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Startup Error",
                             f"Critical dependency missing:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
