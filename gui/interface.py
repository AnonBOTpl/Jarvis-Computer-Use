import customtkinter as ctk
import psutil

class JarvisApp(ctk.CTk):
    """Główne okno aplikacji Jarvis - Agent AI."""

    def __init__(self):
        super().__init__()

        # Stan interfejsu (normalny / kompaktowy)
        self.is_compact = False

        # Konfiguracja głównego okna
        self.title("Jarvis - Asystent AI")
        self.geometry("800x600")

        # Konfiguracja siatki w głównym oknie (grid layout)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # RAMKA GŁÓWNA (ZAWIERAJĄCA LOGI I ELEMENTY STERUJĄCE)
        # ----------------------------------------------------
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # 1. Górny pasek - Stan i Statystyki systemu
        self.top_bar_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar_frame.grid(row=0, column=0, sticky="ew")
        self.top_bar_frame.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            self.top_bar_frame,
            text="Stan: Gotowy do działania",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.stats_label = ctk.CTkLabel(
            self.top_bar_frame,
            text="CPU: 0% | RAM: 0%",
            font=ctk.CTkFont(size=14)
        )
        self.stats_label.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="e")

        # Przycisk trybu kompaktowego w prawym górnym rogu
        self.compact_button = ctk.CTkButton(
            self.top_bar_frame,
            text="Tryb Kompaktowy",
            command=self.toggle_compact_mode,
            width=120
        )
        self.compact_button.grid(row=0, column=2, padx=10, pady=(10, 5), sticky="e")

        # 2. Obszar logów akcji (pole tekstowe z przewijaniem)
        self.log_textbox = ctk.CTkTextbox(
            self.main_frame,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.insert("0.0", "--- Rozpoczęto działanie systemu Jarvis ---\n")
        self.log_textbox.configure(state="disabled") # Tylko do odczytu

        # ----------------------------------------------------
        # RAMKA DOLNA (POLE TEKSTOWE I PRZYCISKI)
        # ----------------------------------------------------
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # Pole wejściowe (Input box dla komend użytkownika)
        self.input_entry = ctk.CTkEntry(
            self.bottom_frame,
            placeholder_text="Wpisz komendę dla Jarvisa..."
        )
        self.input_entry.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")

        # Przycisk "Wykonaj"
        self.execute_button = ctk.CTkButton(
            self.bottom_frame,
            text="Wykonaj",
            command=self.execute_action,
            width=100
        )
        self.execute_button.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Przycisk "Zatrzymaj" (Stop button)
        self.stop_button = ctk.CTkButton(
            self.bottom_frame,
            text="Zatrzymaj",
            fg_color="red",
            hover_color="darkred",
            command=self.stop_action,
            width=100
        )
        self.stop_button.grid(row=0, column=2, padx=0, pady=10)

        # Uruchomienie cyklicznego odświeżania statystyk
        self.update_system_stats()

    def update_system_stats(self):
        """Pobiera i aktualizuje statystyki CPU i RAM."""
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        self.stats_label.configure(text=f"CPU: {cpu_usage}% | RAM: {ram_usage}%")
        # Wywołuj tę samą funkcję co 2000 ms (2 sekundy)
        self.after(2000, self.update_system_stats)

    def toggle_compact_mode(self):
        """Przełącza pomiędzy pełnym a kompaktowym rozmiarem okna."""
        if not self.is_compact:
            # Włączenie trybu kompaktowego
            self.geometry("400x300")
            self.attributes("-topmost", True)  # Zawsze na wierzchu
            self.compact_button.configure(text="Tryb Pełny")
            self.is_compact = True
        else:
            # Powrót do trybu normalnego
            self.geometry("800x600")
            self.attributes("-topmost", False) # Anulowanie zawsze na wierzchu
            self.compact_button.configure(text="Tryb Kompaktowy")
            self.is_compact = False

    def log_message(self, message: str):
        """Dodaje nową wiadomość do obszaru logów."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end") # Przewiń do samego dołu

    def execute_action(self):
        """Metoda wywoływana po kliknięciu przycisku Wykonaj."""
        user_input = self.input_entry.get()
        if user_input:
            self.log_message(f"[UŻYTKOWNIK]: {user_input}")
            self.log_message("[JARVIS]: Przetwarzam zapytanie... (Funkcjonalność w przygotowaniu)")
            self.input_entry.delete(0, "end")
        else:
            self.log_message("[SYSTEM]: Proszę wpisać komendę przed wykonaniem.")

    def stop_action(self):
        """Metoda wywoływana po kliknięciu przycisku Zatrzymaj."""
        self.log_message("[SYSTEM]: Zatrzymywanie aktualnych procesów agenta...")
        self.status_label.configure(text="Stan: Zatrzymany")
