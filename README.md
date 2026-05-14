# Jarvis Computer Use Agent

Zaawansowany agent AI o nazwie **Jarvis** przeznaczony do automatycznego sterowania systemem Windows przy użyciu analizy obrazu i działań w interfejsie graficznym, wykorzystujący moc **Google Gemini API**.

Projekt jest w fazie wczesnego rozwoju, zapewniając modułową architekturę do integracji funkcji rozpoznawania obrazu, analizy ekranu, sterowania klawiaturą oraz myszką.

## Wymagania systemowe

*   System operacyjny: Windows
*   Python: Wersja 3.11 lub nowsza
*   Zmienne środowiskowe: Poprawnie skonfigurowany klucz API dla Google Gemini (szczegóły wkrótce)

## Struktura katalogów

Projekt został podzielony na kilka głównych modułów:

*   `gui/` - Graficzny interfejs użytkownika (CustomTkinter).
*   `vision/` - Przechwytywanie i analiza obrazu z ekranu (mss, Pillow, Gemini).
*   `controller/` - Sterowanie systemem, symulowanie wejścia z klawiatury i myszy (PyAutoGUI).
*   `discovery/` - Funkcje wykrywania i uruchamiania aplikacji na komputerze użytkownika.

## Instalacja i uruchamianie

Najprostszym sposobem na uruchomienie aplikacji jest skorzystanie z dołączonego skryptu automatyzującego.

1.  Pobierz repozytorium.
2.  Uruchom plik `run_jarvis.bat`.

Skrypt `run_jarvis.bat` spróbuje automatycznie:
1.  Wyszukać odpowiednią wersję środowiska Python (min. 3.11).
2.  Zainstalować języka Python za pomocą narzędzia `winget` (jeśli nie zostanie znaleziony w systemie).
    *   **Uwaga:** Automatyczna instalacja przez `winget` może wymagać potwierdzenia okna z prośbą o uprawnienia administratora (UAC).
3.  Utworzyć izolowane wirtualne środowisko `.venv`.
4.  Zainstalować wszystkie wymagane biblioteki, takie jak `google-genai`, `customtkinter`, `pyautogui`, `mss`, `pillow`, czy `rapidfuzz`.
5.  Uruchomić główne okno aplikacji.

Alternatywnie możesz ręcznie skonfigurować środowisko używając pliku `main.py` jako punktu wejścia.

## Uwaga
Wszelki kod, interfejs graficzny i logi są projektowane zgodnie z językiem polskim.
