# Changelog projektu Jarvis

Wszystkie istotne zmiany w tym projekcie będą dokumentowane w tym pliku.

## [Wersja 1.0.0] - Główne wdrożenie integracji ("Top-Tier")

### Zmieniono/Rozbudowano:
*   Zależności poszerzono o najnowsze biblioteki: `pytesseract`, `pygetwindow` oraz `pyperclip`.
*   Skrypt automatycznej instalacji `run_jarvis.bat` zyskał zdolność autowykrywania braku silnika Tesseract w środowisku Windows i zautomatyzował jego proces pobierania dzięki narzędziu `winget`.
*   Wizja stała się inteligentniejsza! Konwersja rzutów całego pulpitu przebiega w sposób zmniejszający ich ostateczny rozmiar, przy zachowaniu odcieni szarości, oszczędzając tokeny kosztownego połączenia z modelem Gemini. Dodano również funkcję "Wizji Selektywnej", zdolną w locie przyciąć screen do rozmiaru dowolnego wywołanego okna przy użyciu biblioteki `pygetwindow`.
*   Asystent Gemini zyskał wsparcie funkcji planowania oraz wsparcie dla wprowadzania komend opartych o systemowy schowek z użyciem biblioteki `pyperclip`. Dodatkowym czynnikiem odciążającym API stała się autokorekta przy wykorzystaniu pakietu OCR.

### Dodano:
*   Baza Złotej Wiedzy! Konkretne i przetestowane zachowania mogą być zapisywane do lokalnego pliku `knowledge.json`, oszczędzając przy wywołaniu 100% użycia pakietu łączącego się do sieci i zmniejszając użycie lokalnych zasobów do absolutnego minimum z wykorzystaniem nowego panelu interfejsu (Bocznego).
*   Lokalny OCR: Jarvis jest w stanie weryfikować komunikaty oraz obecność testów na ekranie przy wykorzystaniu silnika Tesseract (`vision/ocr_engine.py`).

## Wdrożenia starsze:

### Architektura (Faza 1):
*   Przygotowanie katalogów modułowych (gui, vision, controller, discovery).
*   Dodano instrukcje dla interfejsu i instalacji.
*   Wykonano potężny skrypt na wyłapywanie dostępności pakietu Python 3.11+.

### Moduł GUI oraz podstawa PC Use (Faza 2 i 3):
*   Utworzenie podstaw interfejsu użytkownika dla CustomTkinter wraz z czytaniem zużycia podzespołów za pomocą `psutil`.
*   Utworzenie podstaw łączących rzuty ekranu `mss` oraz ruszanie interfejsem za pomocą PyAutoGUI.

### Narzędzie Konfiguracyjne, AI i System App Finder (Faza 4 i 5):
*   Dodano system skanera wyszukującego lokalizację plików EXE za pomocą logiki rozmytej (RapidFuzz) oraz dostępu do Rejestrów i PowerShell.
*   Zaimplementowano obsługę żądań JSON w stronę silnika google-genai.
*   Podpięto logikę pod główny panel sterowania z wykorzystaniem pracy wielowątkowej.
*   Dodano okienko konfiguracji modelu.

### Naprawy Integracyjne:
*   Wyeliminowano fałszywe powiadomienia zwracane podczas skanów Menu Start.
*   Dodano reguły synonimów przyspieszając pracę poszukiwaczy.
*   Sprecyzowano wymagania dotyczące klikania powiązanego ze sztuczną inteligencją w celu wymuszania aktywowania poszczególnych widoków.