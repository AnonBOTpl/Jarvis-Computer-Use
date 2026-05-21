import json
import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QComboBox, QLabel, QHBoxLayout, QMessageBox,
    QButtonGroup, QRadioButton, QGroupBox, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt
from google import genai

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

def load_config():
    defaults = {
        "api_key": "",
        "model_name": "",
        "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        "ai_mode": "api",
        "local_model": "dolphin3:3b",
        "ollama_url": "http://localhost:11434",
        "num_ctx": 4096,
        "debug_mode": True
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for k, v in defaults.items():
                config.setdefault(k, v)
            return config
        except Exception as e:
            logger.error(f"Blad wczytywania konfiguracji: {e}")
    return defaults

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia - Jarvis")
        self.setMinimumWidth(520)
        self.setModal(True)

        self.config = load_config()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Tryb AI ---
        mode_group = QGroupBox("Tryb AI")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_group = QButtonGroup(self)
        self.api_radio = QRadioButton("API (Google Gemini) - z wizja ekranu")
        self.local_radio = QRadioButton("Lokalny (Ollama) - bez wizji, offline")
        self.mode_group.addButton(self.api_radio, 1)
        self.mode_group.addButton(self.local_radio, 2)
        mode_layout.addWidget(self.api_radio)
        mode_layout.addWidget(self.local_radio)

        if self.config.get("ai_mode") == "local":
            self.local_radio.setChecked(True)
        else:
            self.api_radio.setChecked(True)

        layout.addWidget(mode_group)

        # --- API section ---
        self.api_group = QGroupBox("Konfiguracja API Gemini")
        api_form = QFormLayout(self.api_group)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setText(self.config.get("api_key", ""))
        api_form.addRow("Klucz API:", self.api_key_edit)

        fetch_row = QHBoxLayout()
        self.fetch_btn = QPushButton("Pobierz modele")
        self.fetch_status = QLabel("")
        fetch_row.addWidget(self.fetch_btn)
        fetch_row.addWidget(self.fetch_status)
        fetch_row.addStretch()
        api_form.addRow("", fetch_row)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        default_model = self.config.get("model_name", "gemini-2.5-flash")
        self.model_combo.addItem(default_model)
        self.model_combo.setCurrentText(default_model)
        api_form.addRow("Model:", self.model_combo)

        layout.addWidget(self.api_group)

        # --- Local section ---
        self.local_group = QGroupBox("Konfiguracja lokalnego modelu (Ollama)")
        local_form = QFormLayout(self.local_group)

        self.local_model_edit = QLineEdit()
        self.local_model_edit.setText(self.config.get("local_model", "qwen2.5:3b"))
        local_form.addRow("Model Ollamy:", self.local_model_edit)

        self.ollama_url_edit = QLineEdit()
        self.ollama_url_edit.setText(self.config.get("ollama_url", "http://localhost:11434"))
        local_form.addRow("URL Ollamy:", self.ollama_url_edit)

        self.num_ctx_spin = QSpinBox()
        self.num_ctx_spin.setRange(1024, 65536)
        self.num_ctx_spin.setSingleStep(1024)
        self.num_ctx_spin.setValue(self.config.get("num_ctx", 4096))
        self.num_ctx_spin.setToolTip("Limit pamieci kontekstu (tokeny). Wiecej = lepsze zrozumienie, ale wiecej VRAM.")
        local_form.addRow("Limit kontekstu:", self.num_ctx_spin)

        test_row = QHBoxLayout()
        self.test_ollama_btn = QPushButton("Sprawdz polaczenie")
        self.test_ollama_status = QLabel("")
        test_row.addWidget(self.test_ollama_btn)
        test_row.addWidget(self.test_ollama_status)
        test_row.addStretch()
        local_form.addRow("", test_row)

        layout.addWidget(self.local_group)

        # --- Tesseract ---
        tesseract_group = QGroupBox("OCR")
        tesseract_form = QFormLayout(tesseract_group)

        self.tesseract_edit = QLineEdit()
        self.tesseract_edit.setText(self.config.get("tesseract_path", ""))
        tesseract_form.addRow("Sciezka Tesseract:", self.tesseract_edit)

        layout.addWidget(tesseract_group)

        # --- Debug ---
        debug_group = QGroupBox("Debugowanie")
        debug_layout = QVBoxLayout(debug_group)
        self.debug_check = QCheckBox("Pokazuj JARVIS MYŚLI i JARVIS PLANUJE w logach")
        self.debug_check.setChecked(self.config.get("debug_mode", True))
        debug_layout.addWidget(self.debug_check)
        layout.addWidget(debug_group)

        layout.addStretch()

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Zapisz ustawienia")
        self.cancel_btn = QPushButton("Anuluj")
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Connect
        self.fetch_btn.clicked.connect(self._fetch_models)
        self.test_ollama_btn.clicked.connect(self._test_ollama)
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)
        self.mode_group.buttonClicked.connect(self._toggle_mode)

        self._toggle_mode()

    def _toggle_mode(self):
        is_api = self.api_radio.isChecked()
        self.api_group.setEnabled(is_api)
        self.local_group.setEnabled(not is_api)

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
            self.fetch_status.setText("Blad autoryzacji")
            logger.error(f"Blad pobierania modeli: {e}")
            self.model_combo.clear()
            self.model_combo.addItems(["gemini-2.5-flash", "gemini-2.5-pro"])
        finally:
            self.fetch_btn.setEnabled(True)

    def _test_ollama(self):
        import requests
        url = self.ollama_url_edit.text().strip().rstrip("/")

        self.test_ollama_status.setText("Sprawdzanie...")
        self.test_ollama_btn.setEnabled(False)

        try:
            r = requests.get(f"{url}/api/tags", timeout=5)
            if r.status_code == 200:
                models = r.json().get("models", [])
                names = [m.get("name", "") for m in models]
                self.test_ollama_status.setText(f"OK - {len(names)} modeli")
                if names:
                    self.test_ollama_status.setText(f"OK: {', '.join(names[:3])}")
            else:
                self.test_ollama_status.setText("Blad odpowiedzi")
        except requests.exceptions.ConnectionError:
            self.test_ollama_status.setText("Brak polaczenia")
        except Exception as e:
            self.test_ollama_status.setText(f"Blad: {e}")
        finally:
            self.test_ollama_btn.setEnabled(True)

    def _save(self):
        new_config = {
            "api_key": self.api_key_edit.text().strip(),
            "model_name": self.model_combo.currentText().strip(),
            "tesseract_path": self.tesseract_edit.text().strip(),
            "ai_mode": "local" if self.local_radio.isChecked() else "api",
            "local_model": self.local_model_edit.text().strip(),
            "ollama_url": self.ollama_url_edit.text().strip().rstrip("/"),
            "num_ctx": self.num_ctx_spin.value(),
            "debug_mode": self.debug_check.isChecked()
        }
        save_config(new_config)
        QMessageBox.information(self, "Zapisano", "Ustawienia zostaly zapisane.")
        self.accept()
