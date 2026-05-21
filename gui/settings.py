import json
import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QComboBox, QLabel, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
from google import genai

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

def load_config():
    defaults = {"api_key": "", "model_name": "", "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for k, v in defaults.items():
                config.setdefault(k, v)
            return config
        except Exception as e:
            logger.error(f"Błąd wczytywania konfiguracji: {e}")
    return defaults

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia - Jarvis")
        self.setMinimumWidth(500)
        self.setModal(True)

        self.config = load_config()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setText(self.config.get("api_key", ""))
        form.addRow("Klucz API (Google Gemini):", self.api_key_edit)

        fetch_row = QHBoxLayout()
        self.fetch_btn = QPushButton("Pobierz modele")
        self.fetch_status = QLabel("")
        fetch_row.addWidget(self.fetch_btn)
        fetch_row.addWidget(self.fetch_status)
        fetch_row.addStretch()
        form.addRow("", fetch_row)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        default_model = self.config.get("model_name", "gemini-2.5-flash")
        self.model_combo.addItem(default_model)
        self.model_combo.setCurrentText(default_model)
        form.addRow("Wybierz model:", self.model_combo)

        self.tesseract_edit = QLineEdit()
        self.tesseract_edit.setText(self.config.get("tesseract_path", ""))
        form.addRow("Ścieżka Tesseract-OCR:", self.tesseract_edit)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Zapisz ustawienia")
        self.cancel_btn = QPushButton("Anuluj")
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.fetch_btn.clicked.connect(self._fetch_models)
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)

    def _fetch_models(self):
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.fetch_status.setText("Podaj klucz API!")
            return

        self.fetch_status.setText("Pobieranie...")
        self.fetch_btn.setEnabled(False)

        try:
            client = genai.Client(api_key=api_key)
            models_response = client.models.list()
            model_names = []
            for m in models_response:
                if hasattr(m, 'name') and "gemini" in m.name.lower():
                    name = m.name.replace("models/", "") if m.name.startswith("models/") else m.name
                    model_names.append(name)

            if not model_names:
                model_names = ["gemini-2.5-flash", "gemini-2.5-pro"]

            self.model_combo.clear()
            self.model_combo.addItems(model_names)
            saved_model = self.config.get("model_name")
            if saved_model in model_names:
                self.model_combo.setCurrentText(saved_model)
            else:
                self.model_combo.setCurrentText(model_names[0])

            self.fetch_status.setText("Sukces")
        except Exception as e:
            self.fetch_status.setText("Błąd autoryzacji")
            logger.error(f"Błąd pobierania modeli: {e}")
            self.model_combo.clear()
            self.model_combo.addItems(["gemini-2.5-flash", "gemini-2.5-pro"])
        finally:
            self.fetch_btn.setEnabled(True)

    def _save(self):
        new_config = {
            "api_key": self.api_key_edit.text().strip(),
            "model_name": self.model_combo.currentText().strip(),
            "tesseract_path": self.tesseract_edit.text().strip()
        }
        save_config(new_config)
        QMessageBox.information(self, "Zapisano", "Ustawienia zostały zapisane.")
        self.accept()
