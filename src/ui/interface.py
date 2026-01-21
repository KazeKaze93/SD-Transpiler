import pyperclip
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QComboBox, QCheckBox,
                             QLabel, QInputDialog, QLineEdit, QMessageBox)

from src.core.config_loader import config_manager
from src.core.generator import engine
from src.core.llm_worker import GeminiWorker


class TranspilerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SD-Transpiler v2.1")
        self.resize(600, 520)
        self.setMinimumSize(500, 480)

        self.copy_btns = []
        self._ensure_api_key()
        self._init_ui()

    def _ensure_api_key(self):
        key = config_manager.get_api_key()
        if not key:
            self.prompt_api_key()

    def prompt_api_key(self):
        key, ok = QInputDialog.getText(
            self, "API Setup",
            "Enter Google Gemini API Key:",
            QLineEdit.EchoMode.Password
        )
        if ok and key.strip():
            config_manager.save_api_key(key.strip())
        elif ok and not key.strip():
            QMessageBox.warning(self, "Warning", "API Key is required.")

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- 1. Header (Settings + Style) ---
        top_row = QHBoxLayout()

        top_row.addWidget(QLabel("Style:"))
        self.style_selector = QComboBox()
        self.style_selector.addItems(engine.get_style_names())
        self.style_selector.setMinimumWidth(200)
        self.style_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.style_selector.setFixedHeight(32)
        top_row.addWidget(self.style_selector)

        top_row.addStretch()

        self.nsfw_check = QCheckBox("NSFW Mode")
        top_row.addWidget(self.nsfw_check)

        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(42, 32)
        settings_btn.setStyleSheet("font-size: 16px; padding-bottom: 2px;")
        settings_btn.clicked.connect(self.prompt_api_key)
        top_row.addWidget(settings_btn)

        layout.addLayout(top_row)

        # --- 2. Input Area ---
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Describe your idea here (e.g. A cyberpunk samurai)...")
        self.input_text.setMinimumHeight(80)
        layout.addWidget(self.input_text)

        # --- 3. Action Button ---
        self.btn_convert = QPushButton("✨ GENERATE PROMPTS")
        self.btn_convert.setFixedHeight(45)
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setStyleSheet("""
            QPushButton { font-weight: bold; font-size: 14px; background-color: #2563eb; color: white; border-radius: 6px; }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #475569; color: #94a3b8; }
        """)
        self.btn_convert.clicked.connect(self.start_conversion)
        layout.addWidget(self.btn_convert)

        # --- 4. Outputs ---
        self.out_pos = self._build_output_block(layout, "Positive Prompt:",
                                                100)
        self.out_neg = self._build_output_block(layout, "Negative Prompt:", 60,
                                                is_negative=True)

    def _build_output_block(self, parent_layout, label_text, height,
                            is_negative=False):
        container = QVBoxLayout()
        container.setSpacing(2)

        header = QHBoxLayout()
        header.addWidget(QLabel(label_text))
        header.addStretch()

        # FIX 2: Кнопка копирования
        copy_btn = QPushButton("COPY")
        copy_btn.setFixedSize(75, 30)  # 75px ширина, 30px высота
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px; 
                font-weight: bold; 
                border: 1px solid #475569; 
                border-radius: 4px;
                background-color: transparent;
            }
            QPushButton:hover { background-color: #334155; }
        """)

        header.addWidget(copy_btn)
        container.addLayout(header)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFixedHeight(height)

        bg_color = "#2b1a1a" if is_negative else "#0f172a"
        text_edit.setStyleSheet(
            f"background-color: {bg_color}; border: 1px solid #334155; border-radius: 4px; color: #e2e8f0;")

        container.addWidget(text_edit)
        parent_layout.addLayout(container)

        copy_btn.clicked.connect(
            lambda: self.handle_copy(text_edit.toPlainText(), copy_btn))
        return text_edit

    def handle_copy(self, text, btn):
        if not text: return
        pyperclip.copy(text)
        orig = btn.text()
        btn.setText("OK")
        btn.setEnabled(False)
        QTimer.singleShot(1000,
                          lambda: [btn.setText(orig), btn.setEnabled(True)])

    def start_conversion(self):
        user_text = self.input_text.toPlainText().strip()
        if not user_text:
            self.input_text.setFocus()
            return

        api_key = config_manager.get_api_key()
        if not api_key:
            self.prompt_api_key()
            return

        self.set_loading(True)
        self.worker = GeminiWorker(api_key, user_text,
                                   self.style_selector.currentText())
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def set_loading(self, loading: bool):
        self.btn_convert.setEnabled(not loading)
        self.btn_convert.setText(
            "⏳ WORKING..." if loading else "✨ GENERATE PROMPTS")
        self.input_text.setReadOnly(loading)

    def on_success(self, ai_tags):
        result = engine.process(ai_tags, self.style_selector.currentText(),
                                self.nsfw_check.isChecked())
        self.out_pos.setPlainText(result.positive_prompt)
        self.out_neg.setPlainText(result.negative_prompt)
        self.set_loading(False)

    def on_error(self, err_msg):
        self.set_loading(False)
        QMessageBox.critical(self, "Error", err_msg)
        if "API Key" in err_msg:
            self.prompt_api_key()
