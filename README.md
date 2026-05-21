# Jarvis Computer Use Agent

Zaawansowany agent AI do automatycznego sterowania systemem Windows.
Dzia\u0142a w dwoch trybach: przez API Google Gemini (z wizja ekranu) lub lokalnie przez Ollama (bez wizji, offline).

## Wymagania systemowe

*   System: Windows 10/11
*   Python: 3.11+
*   Opcjonalnie: karta NVIDIA z 6GB+ VRAM (dla lokalnego modelu)
*   Opcjonalnie: klucz API Google Gemini (dla trybu API)

## Szybki start

1.  `install.bat` - automatyczna instalacja (Python, zaleznosci, Tesseract, Ollama, model)
2.  `start.bat` - uruchomienie aplikacji
3.  W oknie ustawien wybierz tryb: API (Gemini) lub Lokalny (Ollama)

## Struktura projektu

*   `gui/` - Interfejs PySide6 (Qt), ustawienia, podswietlanie sk\u0142adni, monitor tokenow
*   `vision/` - Przechwytywanie ekranu i OCR (Tesseract)
*   `controller/` - Sterowanie mysza, klawiatura, schowkiem
*   `discovery/` - Wykrywanie i uruchamianie aplikacji (RapidFuzz)
*   `ai_engine/` - Silnik AI: Gemini API (brain.py) lub lokalny Ollama (local_brain.py)
*   `memory/` - System pamieci (Z\u0142ota Lista)
*   `executor/` - Wykonawca skryptow Python/PowerShell

## Komendy g\u0142osne

Jarvis wykonuje komendy tekstowe:
- "otworz notatnik" - uruchamia aplikacje
- "stwórz na pulpicie folder test" - tworzy folder przez skrypt Python
- "wyszukaj w internecie..." - przeszukuje sie\u0107
- "cze\u015b\u0107" - zwyk\u0142a rozmowa

## Tryby AI

| Tryb | Zalety | Wady |
|------|--------|------|
| Gemini API | Wizja ekranu, szybki, dok\u0142adny | Wymaga klucza API, platny |
| Lokalny (Ollama) | Offline, bezp\u0142atny, prywatny | Wolniejszy, bez wizji ekranu |

## Uwaga

Interfejs, logi i komentarze s\u0105 w j\u0119zyku polskim.
