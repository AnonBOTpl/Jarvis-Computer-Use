import os
import sys
import json
import subprocess
import threading
import logging
import time
from collections import deque

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QLineEdit, QPlainTextEdit, QTextEdit,
    QListWidget, QListWidgetItem, QDockWidget, QStatusBar,
    QSplitter, QMessageBox, QFileDialog, QDialog
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QThread, Slot
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QAction, QKeySequence

from gui.settings import SettingsDialog, load_config
from gui.syntax import PythonHighlighter, PowerShellHighlighter
from vision.screen_capture import capture_screen, capture_window_roi, capture_region
from controller.actions import click_at, type_text, press_key, copy_to_clipboard
from discovery.app_scanner import AppScanner
from ai_engine.brain import JarvisBrain
from ai_engine.local_brain import LocalBrain
from memory.knowledge_base import KnowledgeBase
from vision.ocr_engine import is_text_visible, set_tesseract_path
from executor.script_runner import ScriptRunner

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    log = Signal(str, str)
    tokens = Signal(object)
    script_stdout = Signal(str)
    script_stderr = Signal(str)
    script_done = Signal(int, str)
    enable_execute = Signal(bool)
    enable_stop = Signal(bool)
    show_save_button = Signal()
    refresh_sidebar = Signal()
    show_script_preview = Signal(str, str)
    hide_script_preview = Signal()
    set_status_text = Signal(str)


class CommandWorker(QObject):
    def __init__(self, brain, knowledge_base, app_scanner, signals, script_runner):
        super().__init__()
        self.brain = brain
        self.knowledge_base = knowledge_base
        self.app_scanner = app_scanner
        self.signals = signals
        self.script_runner = script_runner
        self._is_running = True
        self.debug_mode = True

    def stop(self):
        self._is_running = False
        self.script_runner.stop_execution()

    @Slot(str)
    def process(self, user_input):
        self.signals.enable_execute.emit(False)
        self.signals.enable_stop.emit(True)

        mem_actions = self.knowledge_base.get_action(user_input)
        if mem_actions:
            self.signals.log.emit("[JARVIS]: Używam zapamiętanej ścieżki.", "blue")
            self._execute_actions(mem_actions, 0, 0, user_input)
            self.signals.enable_execute.emit(True)
            self.signals.enable_stop.emit(False)
            return

        try:
            target_window = ""
            global_offset_x = 0
            global_offset_y = 0
            use_vision_this_turn = False
            last_actions = []
            last_query = ""

            for attempt in range(2):
                if not self._is_running:
                    return

                screenshot = None
                if use_vision_this_turn:
                    if target_window:
                        self.signals.log.emit(
                            f"[JARVIS] (Próba {attempt+1}/2): Pobieram wycinek z okna: '{target_window}'...", "blue"
                        )
                        screenshot, global_offset_x, global_offset_y = capture_window_roi(target_window)
                    if not screenshot:
                        self.signals.log.emit(
                            f"[JARVIS] (Próba {attempt+1}/2): Pobieram obraz z całego ekranu...", "blue"
                        )
                        screenshot = capture_screen(scale_down=True)
                        global_offset_x, global_offset_y = 0, 0

                self.signals.log.emit("[JARVIS]: Wysyłam zapytanie do modelu AI...", "blue")
                response = self.brain.process_request(user_input, screenshot)

                usage = response.get("usage_metadata")
                if usage:
                    self.signals.tokens.emit(usage)

                thought = response.get("thought", "Brak przemyśleń.")
                plan = response.get("plan", [])
                actions = response.get("actions", [])

                suggested_target = response.get("target_window", "")
                if suggested_target:
                    target_window = suggested_target

                if self.debug_mode:
                    self.signals.log.emit(f"[JARVIS MYŚLI]: {thought}", "blue")
                    if plan:
                        self.signals.log.emit(f"[JARVIS PLANUJE]: {', '.join(plan)}", "blue")

                if not actions:
                    self.signals.log.emit("[JARVIS]: Nie znaleziono żadnych akcji do wykonania.", "yellow")
                    break

                if len(actions) == 1 and actions[0].get("type") == "run_code":
                    self.signals.show_script_preview.emit(
                        actions[0].get("code", ""),
                        actions[0].get("language", "python")
                    )
                    return

                elif len(actions) == 1 and actions[0].get("type") == "request_vision":
                    if isinstance(self.brain, LocalBrain):
                        self.signals.log.emit("[JARVIS]: Tryb lokalny - pomijam wizje.", "yellow")
                        use_vision_this_turn = False
                    else:
                        self.signals.log.emit(
                            f"[JARVIS]: {actions[0].get('reason', 'Potrzebuję sprawdzić ekran.')}", "yellow"
                        )
                        use_vision_this_turn = True
                    continue

                else:
                    self._execute_actions(actions, global_offset_x, global_offset_y, user_input)

                    has_error = False
                    if attempt == 0:
                        self.signals.log.emit("[JARVIS]: Weryfikuję rezultat (OCR)...", "blue")

                        verification_screenshot = None
                        last_click_x, last_click_y = None, None

                        for act in reversed(actions):
                            if act.get("type") == "click":
                                last_click_x = act.get("x", 0) + global_offset_x
                                last_click_y = act.get("y", 0) + global_offset_y
                                break

                        if last_click_x is not None and last_click_y is not None:
                            verification_screenshot = capture_region(last_click_x, last_click_y)
                        if not verification_screenshot:
                            verification_screenshot = capture_region(960, 540, size=400)

                        error_keywords = ["błąd", "error", "nie znaleziono", "nie można", "nie udało się", "failed"]
                        for kw in error_keywords:
                            if is_text_visible(verification_screenshot, kw, lang="pol+eng"):
                                self.signals.log.emit(
                                    f"[AUTOKOREKTA]: Wykryto tekst '{kw}' na ekranie. Próbuję innej ścieżki...", "yellow"
                                )
                                has_error = True
                                break

                        if has_error:
                            continue
                        self.signals.log.emit("[JARVIS]: Autokorekta nie wykryła błędów.", "green")

                    self.signals.log.emit("[JARVIS]: Zadanie wykonane.", "green")
                    last_query = user_input
                    last_actions = actions
                    self.last_query = last_query
                    self.last_actions = last_actions
                    self.signals.show_save_button.emit()
                    break

        except Exception as e:
            self.signals.log.emit(f"[BŁĄD WĄTKU]: {e}", "red")
            logger.exception("Błąd w wątku CommandWorker")
        finally:
            self.signals.enable_execute.emit(True)
            self.signals.enable_stop.emit(False)

    def _execute_actions(self, actions, offset_x, offset_y, query):
        for act in actions:
            if not self._is_running:
                break

            action_type = act.get("type")

            if action_type == "click":
                local_x = act.get("x")
                local_y = act.get("y")
                if local_x is None or local_y is None:
                    self.signals.log.emit("[BŁĄD]: Pominięto kliknięcie - brak współrzędnych", "red")
                    continue
                gx, gy = local_x + offset_x, local_y + offset_y
                self.signals.log.emit(f"[JARVIS AKCJA]: Klikam w punkt ({gx}, {gy})", "green")
                try:
                    click_at(gx, gy)
                except Exception as e:
                    self.signals.log.emit(f"[BŁĄD AKCJI]: Nie udało się kliknąć - {e}", "red")

            elif action_type == "type":
                text = act.get("text", "")
                self.signals.log.emit(f"[JARVIS AKCJA]: Wpisuję tekst: '{text}'", "green")
                try:
                    type_text(text)
                except Exception as e:
                    self.signals.log.emit(f"[BŁĄD AKCJI]: Nie udało się wpisać tekstu - {e}", "red")

            elif action_type == "press":
                key = act.get("key", "")
                self.signals.log.emit(f"[JARVIS AKCJA]: Naciskam klawisz '{key}'", "green")
                try:
                    press_key(key)
                except Exception as e:
                    self.signals.log.emit(f"[BŁĄD AKCJI]: Nie udało się wcisnąć klawisza - {e}", "red")

            elif action_type == "run_app":
                query_text = act.get("query", "")
                self.signals.log.emit(f"[JARVIS AKCJA]: Szukam aplikacji: '{query_text}'", "green")
                app_path = self.app_scanner.find_app(query_text)
                if app_path:
                    try:
                        if isinstance(app_path, tuple) and app_path[0] == "aumid":
                            _, aumid = app_path
                            self.signals.log.emit(f"[JARVIS AKCJA]: Uruchamiam AUMID: '{aumid}'", "green")
                            subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{aumid}"])
                        else:
                            self.signals.log.emit(f"[JARVIS AKCJA]: Uruchamiam '{app_path}'", "green")
                            subprocess.Popen(app_path)
                    except Exception as e:
                        self.signals.log.emit(f"[BŁĄD AKCJI]: Nie udało się uruchomić - {e}", "red")
                else:
                    self.signals.log.emit(
                        f"[JARVIS]: Nie znaleziono programu dla: '{query_text}'.", "yellow"
                    )

            elif action_type == "clipboard_write":
                text = act.get("text", "")
                self.signals.log.emit("[JARVIS AKCJA]: Kopiuję do schowka", "green")
                try:
                    copy_to_clipboard(text)
                except Exception as e:
                    self.signals.log.emit(f"[BŁĄD AKCJI]: Nie udało się skopiować - {e}", "red")

            elif action_type == "log_result":
                text = act.get("text", "")
                self.signals.log.emit(f"[JARVIS WYNIK]: {text}", "blue")

            else:
                self.signals.log.emit(f"[OSTRZEŻENIE]: Nierozpoznana akcja: {act}", "yellow")


class ScriptPreviewWorker(QObject):
    def __init__(self, signals, script_runner):
        super().__init__()
        self.signals = signals
        self.script_runner = script_runner
        self._pending_code = ""
        self._pending_lang = "python"
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.script_runner.stop_execution()

    def set_pending(self, code, lang):
        self._pending_code = code
        self._pending_lang = lang

    @Slot()
    def accept(self):
        if not self._pending_code:
            return
        self.signals.hide_script_preview.emit()
        self.signals.log.emit("[SYSTEM]: Uruchamiam skrypt...", "yellow")
        self.signals.enable_stop.emit(True)

        self.script_runner.run_python_code(self._pending_code)

    def reject(self):
        self.signals.hide_script_preview.emit()
        self._pending_code = ""
        self.signals.log.emit("[SYSTEM]: Anulowano wykonanie kodu.", "red")
        self.signals.enable_execute.emit(True)
        self.signals.enable_stop.emit(False)

    def save_to_file(self):
        if not self._pending_code:
            return
        lang = self._pending_lang.lower()
        default_ext = ".py" if lang == "python" else ".ps1"
        filter_str = "Python (*.py)" if lang == "python" else "PowerShell (*.ps1)"
        path, _ = QFileDialog.getSaveFileName(
            None, "Zapisz skrypt", "", filter_str
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._pending_code)
                self.signals.log.emit(f"[SYSTEM]: Zapisano: {path}", "green")
            except Exception as e:
                self.signals.log.emit(f"[BŁĄD ZAPISU]: {e}", "red")


class JarvisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis - Asystent AI")
        self.resize(900, 650)

        self.tokens_in = 0
        self.tokens_out = 0
        self.last_query = ""
        self.last_actions = []
        self.save_action_btn = None
        self.sidebar_visible = False
        self.script_preview_visible = False

        self._setup_signals()
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_workers()
        self._load_styles()

        self.knowledge_base = KnowledgeBase()
        self.app_scanner = AppScanner()

        self.script_runner = ScriptRunner(
            output_callback=lambda t: self.signals.script_stdout.emit(t),
            error_callback=lambda t: self.signals.script_stderr.emit(t),
            finished_callback=lambda c, e: self.signals.script_done.emit(c, e)
        )

        self.brain = None
        self._init_brain()
        self._refresh_sidebar()

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_system_stats)
        self.stats_timer.start(2000)

    def closeEvent(self, event):
        if self.command_worker:
            self.command_worker.stop()
        self.command_thread.quit()
        self.command_thread.wait(1000)
        self.preview_worker.stop()
        self.preview_thread.quit()
        self.preview_thread.wait(1000)

        if isinstance(self.brain, LocalBrain):
            self.brain.cleanup()

        event.accept()

    def _setup_signals(self):
        self.signals = WorkerSignals()
        self.signals.log.connect(self._append_log)
        self.signals.tokens.connect(self._update_tokens)
        self.signals.script_stdout.connect(lambda t: self._append_log(f"> {t}", "green"))
        self.signals.script_stderr.connect(lambda t: self._append_log(f"[BŁĄD SKRYPTU]: {t}", "red"))
        self.signals.script_done.connect(self._on_script_finished)
        self.signals.enable_execute.connect(lambda e: self.execute_btn.setEnabled(e))
        self.signals.enable_stop.connect(lambda e: self.stop_btn.setEnabled(e))
        self.signals.show_save_button.connect(self._show_save_button)
        self.signals.refresh_sidebar.connect(self._refresh_sidebar)
        self.signals.show_script_preview.connect(self._show_script_preview)
        self.signals.hide_script_preview.connect(self._hide_script_preview)
        self.signals.set_status_text.connect(lambda t: self.status_label.setText(t))

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Top bar ---
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 8, 12, 8)

        self.status_label = QLabel("Stan: Gotowy do działania")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.tokens_label = QLabel("Tokeny (In/Out): 0 / 0")
        self.tokens_label.setStyleSheet("color: #f9e2af; font-size: 11px;")

        self.stats_label = QLabel("CPU: 0% | RAM: 0%")
        self.stats_label.setStyleSheet("font-size: 12px;")

        top_layout.addWidget(self.status_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.tokens_label)
        top_layout.addStretch()
        top_layout.addWidget(self.stats_label)
        top_layout.addSpacing(12)

        self.settings_btn = QPushButton("Ustawienia")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.clicked.connect(self._open_settings)
        top_layout.addWidget(self.settings_btn)

        self.sidebar_btn = QPushButton("Złota Lista")
        self.sidebar_btn.setObjectName("sidebarBtn")
        self.sidebar_btn.clicked.connect(self._toggle_sidebar)
        top_layout.addWidget(self.sidebar_btn)

        main_layout.addWidget(top_bar)

        # --- Script preview ---
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(8, 4, 8, 4)

        self.script_edit = QTextEdit()
        self.script_edit.setReadOnly(True)
        self.script_edit.setMinimumHeight(140)
        self.script_edit.setMaximumHeight(300)
        self.script_edit.setFont(QFont("Consolas", 10))
        self.python_highlighter = PythonHighlighter(self.script_edit.document())
        self.ps_highlighter = PowerShellHighlighter(self.script_edit.document())
        self.current_highlighter = self.python_highlighter

        preview_layout.addWidget(self.script_edit)

        btn_row = QHBoxLayout()
        self.accept_btn = QPushButton("Zatwierdź Skrypt")
        self.accept_btn.setObjectName("acceptBtn")
        self.reject_btn = QPushButton("Odrzuć")
        self.reject_btn.setObjectName("rejectBtn")
        self.save_script_btn = QPushButton("Zapisz skrypt")
        self.save_script_btn.setObjectName("saveScriptBtn")
        btn_row.addWidget(self.accept_btn)
        btn_row.addWidget(self.reject_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_script_btn)
        preview_layout.addLayout(btn_row)

        main_layout.addWidget(preview_frame)
        preview_frame.setVisible(False)

        # --- Log area ---
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        self.log_area.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_area.setMaximumBlockCount(5000)
        main_layout.addWidget(self.log_area, stretch=1)

        # --- Bottom bar ---
        bottom_bar = QFrame()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 6, 12, 6)

        self.input_entry = QLineEdit()
        self.input_entry.setPlaceholderText("Wpisz komendę dla Jarvisa...")
        self.input_entry.setFont(QFont("Segoe UI", 11))

        self.execute_btn = QPushButton("Wykonaj")
        self.execute_btn.setObjectName("executeBtn")

        self.stop_btn = QPushButton("Zatrzymaj")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)

        bottom_layout.addWidget(self.input_entry, stretch=1)
        bottom_layout.addSpacing(8)
        bottom_layout.addWidget(self.execute_btn)
        bottom_layout.addWidget(self.stop_btn)

        self.export_log_btn = QPushButton("Zapisz logi")
        self.export_log_btn.setObjectName("exportLogBtn")
        bottom_layout.addWidget(self.export_log_btn)

        main_layout.addWidget(bottom_bar)

        # --- Sidebar dock (Złota Lista) ---
        self.sidebar_dock = QDockWidget("Złota Lista", self)
        self.sidebar_list = QListWidget()
        self.sidebar_list.itemClicked.connect(self._on_sidebar_item_clicked)
        self.sidebar_dock.setWidget(self.sidebar_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sidebar_dock)
        self.sidebar_dock.setVisible(False)

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.cpu_ram_label = QLabel("CPU: 0% | RAM: 0%")
        status_bar.addPermanentWidget(self.cpu_ram_label)
        status_label = QLabel("Gotowy")
        status_bar.addWidget(status_label)

        # Connect buttons
        self.input_entry.returnPressed.connect(self._execute_action)
        self.execute_btn.clicked.connect(self._execute_action)
        self.stop_btn.clicked.connect(self._stop_action)
        self.export_log_btn.clicked.connect(self._export_logs)

    def _setup_shortcuts(self):
        execute_sc = QAction("Wykonaj", self)
        execute_sc.setShortcut(QKeySequence("Ctrl+Return"))
        execute_sc.triggered.connect(self._execute_action)
        self.addAction(execute_sc)

        toggle_sidebar_sc = QAction("Złota Lista", self)
        toggle_sidebar_sc.setShortcut(QKeySequence("Ctrl+B"))
        toggle_sidebar_sc.triggered.connect(self._toggle_sidebar)
        self.addAction(toggle_sidebar_sc)

    def _setup_workers(self):
        self.command_thread = QThread()
        self.command_worker = None

        self.preview_thread = QThread()
        self.preview_worker = ScriptPreviewWorker(self.signals, ScriptRunner(
            output_callback=lambda t: self.signals.script_stdout.emit(t),
            error_callback=lambda t: self.signals.script_stderr.emit(t),
            finished_callback=lambda c, e: self.signals.script_done.emit(c, e)
        ))
        self.preview_worker.moveToThread(self.preview_thread)
        self.preview_thread.start()

        self.accept_btn.clicked.connect(self.preview_worker.accept)
        self.reject_btn.clicked.connect(self.preview_worker.reject)
        self.save_script_btn.clicked.connect(self.preview_worker.save_to_file)

    def _load_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QWidget { color: #cdd6f4; font-family: 'Segoe UI'; font-size: 12px; }
            QFrame#topBar { background-color: #181825; border-bottom: 1px solid #313244; }
            QFrame#bottomBar { background-color: #181825; border-top: 1px solid #313244; }
            QFrame#previewFrame { background-color: #11111b; border-bottom: 1px solid #313244; }
            QPlainTextEdit, QTextEdit {
                background-color: #181825; color: #cdd6f4;
                border: none; padding: 6px;
            }
            QLineEdit {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 8px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
            QPushButton {
                background-color: #45475a; color: #cdd6f4;
                border: none; border-radius: 6px;
                padding: 8px 18px; font-size: 12px;
            }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:pressed { background-color: #313244; }
            QPushButton:disabled { background-color: #313244; color: #585b70; }
            QPushButton#executeBtn { background-color: #89b4fa; color: #1e1e2e; font-weight: bold; }
            QPushButton#executeBtn:hover { background-color: #74c7ec; }
            QPushButton#stopBtn { background-color: #f38ba8; color: #1e1e2e; }
            QPushButton#stopBtn:hover { background-color: #eba0ac; }
            QPushButton#settingsBtn, QPushButton#sidebarBtn {
                background-color: transparent; color: #89b4fa; font-size: 11px;
            }
            QPushButton#settingsBtn:hover, QPushButton#sidebarBtn:hover { color: #74c7ec; }
            QPushButton#acceptBtn { background-color: #a6e3a1; color: #1e1e2e; }
            QPushButton#acceptBtn:hover { background-color: #94e2d5; }
            QPushButton#rejectBtn { background-color: #f38ba8; color: #1e1e2e; }
            QPushButton#saveScriptBtn { background-color: #f9e2af; color: #1e1e2e; }
            QPushButton#exportLogBtn { background-color: #585b70; color: #cdd6f4; font-size: 11px; }
            QPushButton#exportLogBtn:hover { background-color: #6c7086; }
            QDockWidget { background-color: #1e1e2e; color: #cdd6f4; }
            QDockWidget::title { background-color: #181825; padding: 6px; }
            QListWidget { background-color: #181825; color: #cdd6f4; border: none; }
            QListWidget::item { padding: 6px; border-bottom: 1px solid #313244; }
            QListWidget::item:hover { background-color: #313244; }
            QStatusBar { background-color: #181825; border-top: 1px solid #313244; color: #6c7086; }
        """)

    def _init_brain(self):
        config = load_config()
        ai_mode = config.get("ai_mode", "api")

        if ai_mode == "local":
            try:
                self.brain = LocalBrain(config)
                self._append_log("[SYSTEM]: Lokalny model AI (Ollama) załadowany.", "green")
            except Exception as e:
                self._append_log(f"[BŁĄD]: Błąd inicjalizacji modelu lokalnego: {e}", "red")
                self.brain = None
        else:
            if config.get("api_key"):
                try:
                    self.brain = JarvisBrain(config)
                    self._append_log("[SYSTEM]: Silnik AI (Gemini) pomyślnie załadowany.", "green")
                except Exception as e:
                    self._append_log(f"[BŁĄD]: Błąd inicjalizacji silnika AI: {e}", "red")
                    self.brain = None
            else:
                self._append_log(
                    "[SYSTEM]: Brak klucza API. Przejdź do 'Ustawienia', aby skonfigurować.", "yellow"
                )
                self.brain = None

        tesseract_path = config.get("tesseract_path", "")
        if tesseract_path:
            set_tesseract_path(tesseract_path)

        if self.command_worker:
            self.command_worker.debug_mode = config.get("debug_mode", True)

    def _append_log(self, message, tag=None):
        color_map = {
            "blue": QColor("#89b4fa"),
            "green": QColor("#a6e3a1"),
            "red": QColor("#f38ba8"),
            "yellow": QColor("#f9e2af"),
        }
        fmt = QTextCharFormat()
        if tag and tag in color_map:
            fmt.setForeground(color_map[tag])

        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(message + "\n", fmt)
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()

    def _update_tokens(self, usage):
        if usage:
            self.tokens_in += usage.get("prompt_token_count", 0)
            self.tokens_out += usage.get("candidates_token_count", 0)
            self.tokens_label.setText(f"Tokeny (In/Out): {self.tokens_in} / {self.tokens_out}")

    def _update_system_stats(self):
        try:
            import psutil
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            gpu = self._get_gpu_usage()
            self.stats_label.setText(f"CPU: {cpu}% | RAM: {ram}%{gpu}")
            self.cpu_ram_label.setText(f"CPU: {cpu}% | RAM: {ram}%{gpu}")
        except Exception:
            pass

    def _get_gpu_usage(self):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                encoding="utf-8", timeout=3, creationflags=subprocess.CREATE_NO_WINDOW
            )
            parts = out.strip().split(", ")
            if len(parts) == 3:
                gpu_pct = parts[0]
                vram_used = int(parts[1])
                vram_total = int(parts[2])
                vram_pct = round(vram_used / vram_total * 100)
                return f" | GPU: {gpu_pct}% | VRAM: {vram_used}MB/{vram_total}MB ({vram_pct}%)"
        except Exception:
            pass
        return ""

    def _open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._append_log("[SYSTEM]: Ustawienia zaktualizowane.", "green")
            self._init_brain()

    def _toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar_dock.setVisible(self.sidebar_visible)

    def _refresh_sidebar(self):
        self.sidebar_list.clear()
        for query in self.knowledge_base.memory.keys():
            item = QListWidgetItem(query)
            self.sidebar_list.addItem(item)

    def _on_sidebar_item_clicked(self, item):
        query = item.text()
        self.input_entry.setText(query)
        self._execute_action()

    def _show_save_button(self):
        if self.save_action_btn is None or not self.save_action_btn.isVisible():
            btn_layout = self.findChild(QFrame, "bottomBar").layout()
            self.save_action_btn = QPushButton("★ Zapisz Akcję")
            self.save_action_btn.setObjectName("saveActionBtn")
            self.save_action_btn.setStyleSheet("""
                QPushButton { background-color: #f9e2af; color: #1e1e2e;
                              border-radius: 6px; padding: 8px 14px; font-weight: bold; }
                QPushButton:hover { background-color: #f5c2e7; }
            """)
            self.save_action_btn.clicked.connect(self._save_last_action)
            btn_layout.addWidget(self.save_action_btn)

    def _save_last_action(self):
        if self.last_query and self.last_actions:
            self.knowledge_base.add_learned_action(self.last_query, self.last_actions)
            self._append_log(f"[PAMIĘĆ]: Zapisano procedurę dla: '{self.last_query}'", "green")
            self._refresh_sidebar()

    def _execute_action(self):
        user_input = self.input_entry.text().strip()
        if not user_input:
            self._append_log("[SYSTEM]: Proszę wpisać komendę.", "yellow")
            return

        if not self.brain:
            self._append_log("[BŁĄD]: Silnik AI nie jest gotowy. Uzupełnij klucz API.", "red")
            return

        self._append_log(f"[UŻYTKOWNIK]: {user_input}", "blue")
        self.input_entry.clear()

        if self.command_worker:
            self.command_worker.stop()
            self.command_thread.quit()
            self.command_thread.wait()

        self.command_thread = QThread()
        self.command_worker = CommandWorker(
            self.brain, self.knowledge_base, self.app_scanner,
            self.signals, self.script_runner
        )
        self.command_worker.moveToThread(self.command_thread)
        self.command_thread.started.connect(lambda: self.command_worker.process(user_input))
        self.command_thread.start()

    def _stop_action(self):
        self._append_log("[SYSTEM]: Zatrzymywanie procesów...", "yellow")
        self.status_label.setText("Stan: Zatrzymany")
        if self.command_worker:
            self.command_worker.stop()
        self.preview_worker.stop()
        self.execute_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _export_logs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz logi", "jarvis_log.txt", "Plik tekstowy (*.txt)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.log_area.toPlainText())
                self._append_log(f"[SYSTEM]: Logi zapisane do: {path}", "green")
            except Exception as e:
                self._append_log(f"[BŁĄD]: Nie udało się zapisać logów - {e}", "red")

    def _show_script_preview(self, code, lang):
        self.current_highlighter.setDocument(None)
        if lang.lower() in ("powershell", "ps1"):
            self.current_highlighter = self.ps_highlighter
        else:
            self.current_highlighter = self.python_highlighter
        self.current_highlighter.setDocument(self.script_edit.document())

        self.script_edit.setPlainText(code)
        self.preview_worker.set_pending(code, lang)

        preview = self.findChild(QFrame, "previewFrame")
        if preview:
            preview.setVisible(True)

        self._append_log(f"[JARVIS]: Chcę wykonać skrypt ({lang}). Oczekuję na Twoją zgodę.", "blue")

    def _hide_script_preview(self):
        preview = self.findChild(QFrame, "previewFrame")
        if preview:
            preview.setVisible(False)

    def _on_script_finished(self, return_code, stderr_str):
        self._append_log(
            f"[SYSTEM]: Skrypt zakończył pracę z kodem {return_code}.", "yellow"
        )

        if return_code == 0:
            auto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "auto_saved")
            os.makedirs(auto_dir, exist_ok=True)
            timestamp = int(time.time())
            ext = ".py"
            path = os.path.join(auto_dir, f"script_{timestamp}{ext}")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("[auto-saved script]")
                self._append_log(f"[SYSTEM]: Skrypt zarchiwizowano.", "green")
            except Exception as e:
                self._append_log(f"[BŁĄD]: Nie udało się zarchiwizować - {e}", "red")

            self.execute_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        else:
            self._append_log("[JARVIS]: Przechwytuję błąd, próbuję naprawić...", "blue")
            self._process_repair_loop(stderr_str)

    def _process_repair_loop(self, stderr_str):
        if not self.brain or not self.command_worker:
            self.execute_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            return

        repair_prompt = (
            f"Poprzedni kod wygenerował błąd.\n\n"
            f"Oto zwrócony błąd (stderr):\n{stderr_str}\n\n"
            f"Zanalizuj ten błąd, napraw kod i wygeneruj nową wersję operując nadal jako run_code. "
            f"Nie potrzebujesz interfejsu GUI, polegaj wyłącznie na Python/PowerShell."
        )

        try:
            response = self.brain.process_request(repair_prompt, screenshot=None)
            usage = response.get("usage_metadata")
            if usage:
                self._update_tokens(usage)

            actions = response.get("actions", [])
            if len(actions) == 1 and actions[0].get("type") == "run_code":
                code = actions[0].get("code", "")
                lang = actions[0].get("language", "python")
                self._show_script_preview(code, lang)
            else:
                self._append_log("[JARVIS]: Nie potrafię wygenerować poprawki.", "yellow")
                self.execute_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
        except Exception as e:
            self._append_log(f"[BŁĄD NAPRAWY]: {e}", "red")
            self.execute_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
