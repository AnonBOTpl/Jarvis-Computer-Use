import logging
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QMenu
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)

SPINNER_CHARS = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]

# Ceny za 1M tokenow (USD) - stan na 2026
MODEL_PRICING = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
    "default": {"input": 0.15, "output": 0.60},
}


class TokenMonitor(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tokenMonitor")
        self.setFixedWidth(200)

        self.tokens_in = 0
        self.tokens_out = 0
        self.max_context = 4096
        self.model_name = "default"
        self.is_local = False
        self._spinner_idx = 0
        self._loading = False

        self._setup_ui()

        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._spin)
        self._spinner_timer.start(200)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.spinner_label = QLabel(" ")
        self.spinner_label.setFixedWidth(16)
        self.spinner_label.setStyleSheet("color: #89b4fa; font-size: 14px;")
        top_row.addWidget(self.spinner_label)

        top_row.addStretch()

        self.options_btn = QPushButton("...")
        self.options_btn.setObjectName("tokenOptionsBtn")
        self.options_btn.setFixedSize(20, 20)
        self.options_btn.setFlat(True)
        self.options_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.options_menu = QMenu(self)
        self.options_menu.addAction("Resetuj liczniki", self.reset)
        self.options_btn.clicked.connect(self._show_options)
        top_row.addWidget(self.options_btn)

        layout.addLayout(top_row)

        self.tokens_label = QLabel("0 Tokeny")
        self.tokens_label.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.tokens_label)

        self.context_label = QLabel("0% Uzycie kontekstu")
        self.context_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(self.context_label)

        self.cost_label = QLabel("0,00 USD Koszt")
        self.cost_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(self.cost_label)

    def _show_options(self):
        self.options_menu.exec(self.options_btn.mapToGlobal(self.options_btn.rect().bottomLeft()))

    def reset(self):
        self.tokens_in = 0
        self.tokens_out = 0
        self._update_display()

    def set_loading(self, loading: bool):
        self._loading = loading
        self.spinner_label.setText(" " if not loading else SPINNER_CHARS[0])

    def _spin(self):
        if self._loading:
            self._spinner_idx = (self._spinner_idx + 1) % len(SPINNER_CHARS)
            self.spinner_label.setText(SPINNER_CHARS[self._spinner_idx])

    def set_model(self, model_name: str, max_context: int, is_local: bool):
        self.model_name = model_name
        self.max_context = max_context
        self.is_local = is_local
        self._update_display()

    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        self.tokens_in += prompt_tokens
        self.tokens_out += completion_tokens
        self._update_display()

    def _update_display(self):
        total = self.tokens_in + self.tokens_out
        self.tokens_label.setText(f"{total:,} Tokeny".replace(",", " "))

        if self.max_context > 0:
            pct = round(total / self.max_context * 100)
            self.context_label.setText(f"{pct}% Uzycie kontekstu")
        else:
            self.context_label.setText("--% Uzycie kontekstu")

        if self.is_local:
            self.cost_label.setText("Lokalny - brak kosztow")
        else:
            pricing = MODEL_PRICING.get(self.model_name, MODEL_PRICING["default"])
            cost = (self.tokens_in / 1_000_000 * pricing["input"] +
                    self.tokens_out / 1_000_000 * pricing["output"])
            self.cost_label.setText(f"{cost:.2f} USD Koszt")
