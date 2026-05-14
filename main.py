import sys
import os

# Dodanie ścieżki projektu do zmiennej systemowej, by moduły widziały się nawzajem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.interface import JarvisApp
import customtkinter as ctk

def main():
    """Główny punkt wejścia do aplikacji Jarvis."""

    # Ustawienie trybu wyglądu i koloru przewodniego interfejsu
    ctk.set_appearance_mode("System")  # System dopasowuje się do ustawień OS (Ciemny/Jasny)
    ctk.set_default_color_theme("blue")  # Dostępne wbudowane motywy: blue, dark-blue, green

    # Inicjalizacja głównego okna aplikacji zdefiniowanego w module gui
    app = JarvisApp()

    # Uruchomienie pętli głównej interfejsu graficznego
    app.mainloop()

if __name__ == "__main__":
    main()
