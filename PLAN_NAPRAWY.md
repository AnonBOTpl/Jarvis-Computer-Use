# Plan Naprawy — Jarvis Computer-Use Agent

## Faza 1: Krytyczne bugi ✅ (wykonane)

### 1.1. Bezpieczeństwo — .gitignore
Dodano `knowledge.json`, `scripts/auto_saved/`, `temp_agent_script.py` do `.gitignore`.

### 1.2. temp_agent_script.py — race condition
**Plik:** `executor/script_runner.py` — UUID w nazwie pliku, `except: pass` → `except OSError` z logger.

### 1.3. PowerShell encoding
**Plik:** `executor/script_runner.py` — Wykrywanie wersji PowerShell, UTF-8 zamiast CP852.

### 1.4. JSON.parse crash w app_scanner
**Plik:** `discovery/app_scanner.py` — Pełny rewrite: walidacja JSON, AUMID fallback, caching 60s.

### 1.5. Konflikt tagów kolorystycznych → **ZASTĄPIONY przez PySide6 QSyntaxHighlighter**
### 1.7. Walidacja None w click → **PRZENIESIONE do nowego interface.py PySide6**

---

## Faza 2: Migracja GUI — CustomTkinter → PySide6 (bieżąca)

### Cel
Przepisać cały `gui/` z CustomTkinter na PySide6 (Qt6 dla Python).

### Uzasadnienie
- **QSyntaxHighlighter** — wbudowane podświetlanie składni, bez Pygments i hacków z tagami
- **QThread + Signals/Slots** — bezpieczna wielowątkowość, bez `after(0, lambda)`
- **QSS** — dowolny wygląd (dark theme jak VS Code)
- **QPlainTextEdit** — logi przy milionach linii bez lagów
- **QDockWidget / QSplitter** — natywny podział paneli

### 2.1. Struktura nowego GUI

```
gui/
├── __init__.py
├── interface.py      ← QMainWindow (główne okno)
├── settings.py       ← QDialog (ustawienia)
└── syntax.py         ← QSyntaxHighlighter (Python/PowerShell)
```

### 2.2. Layout nowego okna

```
QMainWindow
├── CentralWidget (QSplitter Vertical)
│   ├── TopBar (QFrame — status, tokeny, statystyki, przyciski)
│   ├── ScriptPreview (QTextEdit + SyntaxHighlighter, domyślnie hidden)
│   ├── LogArea (QPlainTextEdit — stdout/stderr z kolorami)
│   └── BottomBar (QLineEdit + Wykonaj + Zatrzymaj + Zapisz)
├── RightDock (QListWidget — Złota Lista)
└── QStatusBar (CPU | RAM | Tokeny In/Out)
```

### 2.3. Obsługa wątków

Zamiast `threading.Thread` + `after(0, _append_log)`:
- `QThread` dla `_process_command`
- `Signal(str, str)` do logowania — emitujesz sygnał, Qt kolejuje w main thread
- `Signal(dict)` do aktualizacji tokenów

### 2.4. Pliki do zmiany

| Plik | Operacja |
|------|----------|
| `requirements.txt` | `customtkinter` → `PySide6` |
| `gui/interface.py` | **Przepisać** — QMainWindow z QPlainTextEdit, QSyntaxHighlighter, QThread |
| `gui/settings.py` | **Przepisać** — QDialog z QFormLayout |
| `gui/syntax.py` | **Dodać** — QSyntaxHighlighter dla Python/PowerShell |
| `main.py` | **Zmienić** — QApplication zamiast CTk |
| `gui/__init__.py` | Zostaje pusty |

### 2.5. Lista zastąpień widgetów

| CustomTkinter | PySide6 |
|---------------|---------|
| `CTk` | `QMainWindow` |
| `CTkFrame` | `QFrame` / `QWidget` |
| `CTkLabel` | `QLabel` |
| `CTkButton` | `QPushButton` (z QSS stylowaniem) |
| `CTkEntry` | `QLineEdit` |
| `CTkTextbox` | `QPlainTextEdit` (logi) / `QTextEdit` (podgląd) |
| `CTkScrollableFrame` | `QListWidget` / `QScrollArea` |
| `CTkToplevel` | `QDialog` |
| `CTkOptionMenu` | `QComboBox` |
| `CTkFont` | `QFont` |
| `after(ms, cb)` | `QTimer.singleShot(ms, cb)` |

---

## Faza 3: Wydajność (po migracji GUI)

### 3.1. Caching app_scanner ✅ (wykonane)
### 3.2. Lepsze regiony OCR → **do implementacji w nowym interface.py**
### 3.3. Konfigurowalny język OCR ✅ (wykonane)
### 3.4. Leniwe Pygments → **NIE DOTYCZY — zastąpione QSyntaxHighlighter**

---

## Faza 4: Jakość kodu

### 4.1. Usunąć pusty plik ✅ (wykonane)
### 4.2. Naprawić importy w `actions.py` ✅ (wykonane)
### 4.3. Dodać logging framework ✅ (wykonane)
### 4.4. Walidacja odpowiedzi AI ✅ (wykonane)
### 4.5. Sztywne ścieżki → konfigurowalne ✅ (wykonane)

---

## Faza 5: Nowe funkcje (po migracji)

### 5.1. Skróty klawiszowe
- `Ctrl+Enter` = wykonaj
- `Ctrl+S` = zapisz skrypt
- `Ctrl+Shift+S` = zapisz akcję

### 5.2. Logowanie do pliku
- Dodać `QFileDialog` do wyboru pliku logu

### 5.3. Multi-monitor support
- Iterować po `sct.monitors` zamiast `[1]`

---

## Podsumowanie plików

| Plik | Status |
|------|--------|
| `.gitignore` | ✅ |
| `executor/script_runner.py` | ✅ |
| `discovery/app_scanner.py` | ✅ |
| `gui/interface.py` | 🔄 Migracja do PySide6 |
| `gui/settings.py` | 🔄 Migracja do PySide6 |
| `gui/syntax.py` | 🆕 Nowy plik |
| `vision/ocr_engine.py` | ✅ |
| `vision/screen_capture.py` | ✅ |
| `controller/actions.py` | ✅ |
| `controller/mouse_keyboard.py` | ✅ Usunięty |
| `config.json` | ✅ |
| `main.py` | 🔄 Dostosowanie do PySide6 |
| `requirements.txt` | 🔄 `customtkinter` → `PySide6` |
