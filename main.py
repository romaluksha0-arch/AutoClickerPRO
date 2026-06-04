
import json
import sys
import threading
import time
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSpinBox, QComboBox, QLineEdit, QFrame, QMessageBox
)

from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Listener, Key

SETTINGS_FILE = Path("settings.json")


class Signals(QObject):
    update_stats = pyqtSignal(int)
    set_status = pyqtSignal(str)


class AutoClickerPro(QWidget):
    def __init__(self):
        super().__init__()
        self.running = False
        self.click_count = 0
        self.capture_next_key = False

        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.signals = Signals()

        self.signals.update_stats.connect(self.update_clicks_label)
        self.signals.set_status.connect(self.set_status)

        self.setup_ui()
        self.load_settings()
        self.setup_hotkeys()

    def setup_ui(self):
        self.setWindowTitle("AutoClicker Pro")
        self.resize(760, 520)

        self.setStyleSheet("""
            QWidget {
                background: #080808;
                color: #f5f5f5;
                font-size: 14px;
                font-family: Arial;
            }
            QLabel#Title {
                font-size: 34px;
                font-weight: 900;
                letter-spacing: 2px;
            }
            QLabel#Subtitle {
                color: #bdbdbd;
            }
            QLabel#Status {
                background: #111111;
                border: 1px solid #333333;
                border-radius: 14px;
                padding: 12px;
                color: #ffffff;
                font-weight: bold;
            }
            QFrame#Card {
                background: #111111;
                border: 1px solid #2c2c2c;
                border-radius: 18px;
                padding: 16px;
            }
            QPushButton {
                background: #ffffff;
                color: #000000;
                border: none;
                padding: 13px;
                border-radius: 12px;
                font-weight: 900;
            }
            QPushButton:hover {
                background: #dcdcdc;
            }
            QPushButton#StopButton, QPushButton#DarkButton {
                background: #1d1d1d;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QPushButton#StopButton:hover, QPushButton#DarkButton:hover {
                background: #292929;
            }
            QSpinBox, QComboBox, QLineEdit {
                background: #070707;
                border: 1px solid #444444;
                border-radius: 10px;
                padding: 10px;
                color: #ffffff;
            }
            QSpinBox:focus, QComboBox:focus, QLineEdit:focus {
                border: 1px solid #ffffff;
            }
        """)

        root = QVBoxLayout()
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        title = QLabel("AUTOCLICKER PRO")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Мышь • Клавиатура • Интервалы • Хоткеи • Статистика • Сохранение настроек")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root.addWidget(title)
        root.addWidget(subtitle)

        self.status_label = QLabel("Статус: выключен | F6 — старт/стоп | F7 — выход")
        self.status_label.setObjectName("Status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        grid = QGridLayout()
        grid.setSpacing(16)

        settings_card = self.make_card()
        settings_layout = QVBoxLayout(settings_card)

        settings_title = QLabel("Настройки")
        settings_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        settings_layout.addWidget(settings_title)

        self.interval_box = QSpinBox()
        self.interval_box.setRange(1, 60000)
        self.interval_box.setValue(100)
        self.interval_box.setSuffix(" мс")

        self.mode_box = QComboBox()
        self.mode_box.addItems(["Мышь", "Клавиатура"])

        self.mouse_button_box = QComboBox()
        self.mouse_button_box.addItems(["Левая кнопка", "Правая кнопка", "Средняя кнопка"])

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Например: space, e, r, shift")
        self.key_input.setText("space")

        self.capture_button = QPushButton("Выбрать клавишу нажатием")
        self.capture_button.clicked.connect(self.start_key_capture)

        self.click_type_box = QComboBox()
        self.click_type_box.addItems(["Одинарный клик", "Двойной клик"])

        settings_layout.addWidget(QLabel("Интервал"))
        settings_layout.addWidget(self.interval_box)
        settings_layout.addWidget(QLabel("Режим"))
        settings_layout.addWidget(self.mode_box)
        settings_layout.addWidget(QLabel("Кнопка мыши"))
        settings_layout.addWidget(self.mouse_button_box)
        settings_layout.addWidget(QLabel("Клавиша клавиатуры"))
        settings_layout.addWidget(self.key_input)
        settings_layout.addWidget(self.capture_button)
        settings_layout.addWidget(QLabel("Тип действия"))
        settings_layout.addWidget(self.click_type_box)

        grid.addWidget(settings_card, 0, 0)

        stats_card = self.make_card()
        stats_layout = QVBoxLayout(stats_card)

        stats_title = QLabel("Статистика")
        stats_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        stats_layout.addWidget(stats_title)

        self.clicks_label = QLabel("Сделано действий: 0")
        self.clicks_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.clicks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_settings_label = QLabel("")
        self.current_settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_settings_label.setStyleSheet("color: #cfcfcf;")

        self.reset_stats_btn = QPushButton("Сбросить статистику")
        self.reset_stats_btn.setObjectName("DarkButton")
        self.reset_stats_btn.clicked.connect(self.reset_stats)

        stats_layout.addStretch()
        stats_layout.addWidget(self.clicks_label)
        stats_layout.addWidget(self.current_settings_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.reset_stats_btn)

        grid.addWidget(stats_card, 0, 1)
        root.addLayout(grid)

        buttons = QHBoxLayout()

        self.start_btn = QPushButton("START / F6")
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setObjectName("StopButton")
        self.save_btn = QPushButton("Сохранить настройки")
        self.save_btn.setObjectName("DarkButton")

        self.start_btn.clicked.connect(self.toggle_clicker)
        self.stop_btn.clicked.connect(self.stop_clicker)
        self.save_btn.clicked.connect(self.save_settings)

        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addWidget(self.save_btn)

        root.addLayout(buttons)
        self.setLayout(root)

        self.mode_box.currentTextChanged.connect(self.refresh_current_settings)
        self.interval_box.valueChanged.connect(self.refresh_current_settings)
        self.mouse_button_box.currentTextChanged.connect(self.refresh_current_settings)
        self.key_input.textChanged.connect(self.refresh_current_settings)
        self.click_type_box.currentTextChanged.connect(self.refresh_current_settings)

        self.refresh_current_settings()

    def make_card(self):
        card = QFrame()
        card.setObjectName("Card")
        return card

    def setup_hotkeys(self):
        def on_press(key):
            try:
                if self.capture_next_key:
                    value = self.key_to_text(key)
                    self.key_input.setText(value)
                    self.capture_next_key = False
                    self.set_status("Клавиша выбрана: " + value)
                    return

                if key == Key.f6:
                    self.toggle_clicker()

                if key == Key.f7:
                    self.stop_clicker()
                    QApplication.quit()
            except Exception:
                pass

        self.listener = Listener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()

    def key_to_text(self, key):
        if hasattr(key, "char") and key.char:
            return key.char

        text = str(key).replace("Key.", "")
        aliases = {
            "space": "space",
            "shift": "shift",
            "shift_r": "shift",
            "ctrl_l": "ctrl",
            "ctrl_r": "ctrl",
            "alt_l": "alt",
            "alt_r": "alt",
            "enter": "enter",
            "tab": "tab",
            "esc": "esc",
            "backspace": "backspace",
        }
        return aliases.get(text, text)

    def start_key_capture(self):
        self.capture_next_key = True
        self.set_status("Нажми любую клавишу для выбора...")

    def get_mouse_button(self):
        selected = self.mouse_button_box.currentText()
        if selected == "Левая кнопка":
            return Button.left
        if selected == "Правая кнопка":
            return Button.right
        return Button.middle

    def get_keyboard_key(self):
        value = self.key_input.text().strip().lower()

        special = {
            "space": Key.space,
            "enter": Key.enter,
            "tab": Key.tab,
            "esc": Key.esc,
            "escape": Key.esc,
            "shift": Key.shift,
            "ctrl": Key.ctrl,
            "alt": Key.alt,
            "backspace": Key.backspace,
        }

        if value in special:
            return special[value]

        if len(value) == 1:
            return value

        return value

    def worker(self):
        while self.running:
            try:
                mode = self.mode_box.currentText()
                click_type = self.click_type_box.currentText()
                count = 2 if click_type == "Двойной клик" else 1

                if mode == "Мышь":
                    self.mouse.click(self.get_mouse_button(), count)

                elif mode == "Клавиатура":
                    key = self.get_keyboard_key()
                    for _ in range(count):
                        self.keyboard.press(key)
                        self.keyboard.release(key)

                self.click_count += count
                self.signals.update_stats.emit(self.click_count)

                time.sleep(self.interval_box.value() / 1000)

            except Exception as error:
                self.running = False
                self.signals.set_status.emit("Ошибка: " + str(error))
                break

    def toggle_clicker(self):
        if self.running:
            self.stop_clicker()
        else:
            self.start_clicker()

    def start_clicker(self):
        if self.running:
            return

        self.running = True
        self.set_status("Статус: работает | F6 — остановить")
        self.refresh_current_settings()
        threading.Thread(target=self.worker, daemon=True).start()

    def stop_clicker(self):
        self.running = False
        self.set_status("Статус: выключен | F6 — старт/стоп | F7 — выход")

    def reset_stats(self):
        self.click_count = 0
        self.update_clicks_label(0)

    def update_clicks_label(self, count):
        self.clicks_label.setText(f"Сделано действий: {count}")

    def set_status(self, text):
        self.status_label.setText(text)

    def refresh_current_settings(self):
        self.current_settings_label.setText(
            f"{self.mode_box.currentText()} | {self.interval_box.value()} мс | "
            f"{self.mouse_button_box.currentText()} | клавиша: {self.key_input.text()}"
        )

    def save_settings(self):
        data = {
            "interval": self.interval_box.value(),
            "mode": self.mode_box.currentText(),
            "mouse_button": self.mouse_button_box.currentText(),
            "key": self.key_input.text(),
            "click_type": self.click_type_box.currentText(),
        }

        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Сохранено", "Настройки сохранены в settings.json")

    def load_settings(self):
        if not SETTINGS_FILE.exists():
            return

        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            self.interval_box.setValue(data.get("interval", 100))
            self.mode_box.setCurrentText(data.get("mode", "Мышь"))
            self.mouse_button_box.setCurrentText(data.get("mouse_button", "Левая кнопка"))
            self.key_input.setText(data.get("key", "space"))
            self.click_type_box.setCurrentText(data.get("click_type", "Одинарный клик"))
        except Exception:
            pass

    def closeEvent(self, event):
        self.stop_clicker()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoClickerPro()
    window.show()
    sys.exit(app.exec())
