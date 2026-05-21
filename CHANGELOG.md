# Changelog

## [1.1.0] - 2026-05-21

### Dodano
- Obs\u0142uga lokalnego modelu AI przez Ollama (LocalBrain)
- Widget Token Monitor (tokeny, uzycie kontekstu, koszt)
- Monitorowanie GPU i VRAM (nvidia-smi)
- Opcja debugowania w ustawieniach (pokazuj/ukrywaj JARVIS MY\u015aLI)
- Limit kontekstu (num_ctx) dla lokalnego modelu w ustawieniach
- Wskaznik ladowania (spinner) podczas generowania odpowiedzi
- start.bat - lekki launcher aplikacji

### Zmieniono
- Migracja GUI z CustomTkinter na PySide6 (Qt)
- Domy\u015blny model lokalny: sam860/dolphin3-qwen2.5:3b (bez cenzury)
- Przepisano instalator (install.bat) - warunkowe instalowanie, bez reinstalacji .venv
- Naprawiono blokowanie UI podczas pracy modelu (GPU async + threading)
- System prompt dla lepszego generowania akcji (szczeg\u00f3lnie dla lokalnego modelu)
- Statystyki CPU/RAM/GPU przeniesione tylko do dolnego paska (bez duplikatu u g\u00f3ry)

### Naprawiono
- Blad parsowania w install.bat (`. was unexpected`)
- Backslash w skryptach Python (zamiana \ na /)
- Czyszczenie modelu z GPU przy zamykaniu aplikacji
- Signal leak w repai loop (wielokrotne pod\u0142\u0105czanie sygna\u0142u repair)
- DPI warning (SetProcessDpiAwarenessContext)

## [1.0.0] - 2026-05

### Dodano
- Pierwsza wersja z GUI (CustomTkinter)
- Obs\u0142uga API Google Gemini
- OCR przez Tesseract
- Wykrywanie aplikacji (RapidFuzz)
- Z\u0142ota Lista (pami\u0119\u0107 akcji)
- Wykonawca skrypt\u00f3w Python/PowerShell
