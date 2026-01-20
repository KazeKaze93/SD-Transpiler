from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QComboBox, QCheckBox,
                             QLabel, QFrame, QListView, QInputDialog,
                             QLineEdit)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import pyperclip
import base64

from src.core.generator import engine
from src.core.config_loader import config_manager
from src.core.llm_worker import GeminiWorker

# Вшитые SVG иконки
ICON_COPY = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzYjgyZjYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB4PSI5IiB5PSI5IiB3aWR0aD0iMTMiIGhlaWdodD0iMTMiIHJ4PSIyIiByeT0iMiI+PC9yZWN0PjxwYXRoIGQ9Ik01IDE1SDNhMiAyIDAgMCAxLTItMlY1YTIgMiAwIDAgMSAyLTJoMTBhMiAyIDAgMCAxIDIgMiAyIDIiPjwvcGF0aD48L3N2Zz4="
ICON_CHECK = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMyMmNiNWUiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIyMCA2IDkgMTcgNCAxMiI+PC9wb2x5bGluZT48L3N2Zz4="


class TranspilerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SD-Transpiler v1.0")
        self.setMinimumSize(600, 750)
        self.copy_btns = []  # Для управления анимацией галочек
        self._ensure_api_key()
        self._init_ui()

    def _get_icon(self, b64):
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(b64), "SVG")
        return QIcon(pixmap)

    def _ensure_api_key(self):
        """Всплывающее окно вместо поля в UI"""
        key = config_manager.get_api_key()
        if not key or not key.strip():
            new_key, ok = QInputDialog.getText(self, "API Key Required",
                                               "Enter Gemini API Key:",
                                               QLineEdit.Password)
            if ok and new_key.strip():
                config_manager.save_api_key(new_key.strip())

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. Styles & NSFW
        top_row = QHBoxLayout()
        self.style_selector = QComboBox()
        self.style_selector.setView(QListView())  # Твой фикс для дропдауна
        self.style_selector.addItems(engine.get_style_names())
        self.style_selector.currentIndexChanged.connect(self.reset_icons)

        self.nsfw_check = QCheckBox("NSFW Mode")
        self.nsfw_check.setStyleSheet(
            "QCheckBox::indicator { width: 22px; height: 22px; border: 2px solid #3b82f6; border-radius: 4px; } QCheckBox::indicator:checked { background: #3b82f6; }")
        self.nsfw_check.stateChanged.connect(self.reset_icons)

        top_row.addWidget(QLabel("STYLE:"), 0)
        top_row.addWidget(self.style_selector, 1)
        top_row.addWidget(self.nsfw_check, 0)
        layout.addLayout(top_row)

        # 2. Input
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Describe your masterpiece...")
        self.input_text.textChanged.connect(self.reset_icons)
        layout.addWidget(QLabel("USER REQUEST:"))
        layout.addWidget(self.input_text)

        # 3. Action
        self.btn_convert = QPushButton("CONVERT TO MASTERPIECE")
        self.btn_convert.setFixedHeight(55)
        self.btn_convert.setStyleSheet(
            "background: #3b82f6; color: white; font-weight: bold; border-radius: 10px;")
        self.btn_convert.clicked.connect(self.start_conversion)
        layout.addWidget(self.btn_convert)

        # 4. Outputs
        self.out_pos = self._build_output(layout, "POSITIVE PROMPT", 150)
        self.out_neg = self._build_output(layout, "NEGATIVE PROMPT", 100,
                                          is_neg=True)

    def _build_output(self, parent_layout, label_text, height, is_neg=False):
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(label_text))
        h_layout.addStretch()

        copy_btn = QPushButton()
        copy_btn.setIcon(self._get_icon(ICON_COPY))
        copy_btn.setIconSize(QSize(20, 20))
        copy_btn.setFixedSize(32, 32)
        copy_btn.setStyleSheet(
            "background: transparent; border: 1px solid #334155; border-radius: 6px;")

        self.copy_btns.append(copy_btn)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFixedHeight(height)
        color = "#f87171" if is_neg else "#f8fafc"
        text_edit.setStyleSheet(
            f"border: 1px solid #334155; background: #1e293b; color: {color}; border-radius: 8px;")

        h_layout.addWidget(copy_btn)
        parent_layout.addLayout(h_layout)
        parent_layout.addWidget(text_edit)

        copy_btn.clicked.connect(
            lambda: self.handle_copy(text_edit.toPlainText(), copy_btn))
        return text_edit

    def handle_copy(self, text, btn):
        if text:
            pyperclip.copy(text)
            self.reset_icons()
            btn.setIcon(
                self._get_icon(ICON_CHECK))  # Анимация: превращаем в галочку

    def reset_icons(self):
        """Сброс всех иконок к исходному состоянию"""
        for btn in self.copy_btns:
            btn.setIcon(self._get_icon(ICON_COPY))

    def mousePressEvent(self, event):
        """Сброс иконок при клике в любое место окна"""
        self.reset_icons()
        super().mousePressEvent(event)

    def start_conversion(self):
        self.reset_icons()
        user_input = self.input_text.toPlainText().strip()
        if not user_input: return
        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("GENERATING...")
        self.worker = GeminiWorker(config_manager.get_api_key(), user_input,
                                   self.style_selector.currentText())
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, ai_tags):
        res = engine.process(ai_tags, self.style_selector.currentText())
        self.out_pos.setPlainText(res.positive_prompt)
        neg = res.negative_prompt
        if not self.nsfw_check.isChecked(): neg += ", nsfw, nude, naked, sex"
        self.out_neg.setPlainText(neg)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("CONVERT TO MASTERPIECE")

    def on_error(self, err):
        self.out_pos.setPlainText(f"AI ERROR: {err}")
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("CONVERT TO MASTERPIECE")