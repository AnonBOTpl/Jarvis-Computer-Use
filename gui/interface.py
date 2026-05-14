import customtkinter as ctk
import psutil
import threading
import os
import subprocess
from gui.settings import SettingsWindow, load_config
from vision.screen_capture import capture_screen, capture_window_roi, capture_region
from controller.actions import click_at, type_text, press_key, copy_to_clipboard
from discovery.app_scanner import AppScanner
from ai_engine.brain import JarvisBrain
from memory.knowledge_base import KnowledgeBase
from vision.ocr_engine import is_text_visible

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
        self.top_bar_frame.grid_columnconfigure(2, weight=1)

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

        # Przycisk Ustawienia
        self.settings_button = ctk.CTkButton(
            self.top_bar_frame,
            text="Ustawienia",
            command=self.open_settings,
            width=100
        )
        self.settings_button.grid(row=0, column=3, padx=(0, 10), pady=(10, 5), sticky="e")

        # Przycisk Bocznego Panelu "Ostatnie Akcje"
        self.sidebar_button = ctk.CTkButton(
            self.top_bar_frame,
            text="Ostatnie Akcje",
            command=self.toggle_sidebar,
            width=120
        )
        self.sidebar_button.grid(row=0, column=4, padx=(0, 10), pady=(10, 5), sticky="e")

        # --- Obszar dzielący na Logi (lewo) i Panel Akcji (prawo) ---
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # 2. Obszar logów akcji (pole tekstowe z przewijaniem) w środku nowej ramki
        self.log_textbox = ctk.CTkTextbox(
            self.content_frame,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.insert("0.0", "--- Rozpoczęto działanie systemu Jarvis ---\n")
        self.log_textbox.configure(state="disabled") # Tylko do odczytu

        # Panel boczny na ostanie akcje i zapis z pamięci
        self.sidebar_frame = ctk.CTkScrollableFrame(self.content_frame, width=200, label_text="Złota Lista")
        self.sidebar_visible = False

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

        # Inicjalizacja modułów Jarvis
        self.knowledge_base = KnowledgeBase()
        self.app_scanner = AppScanner()
        self.brain = None
        self.last_query = ""
        self.last_actions = []
        self._init_brain()
        self._refresh_sidebar()

    def _init_brain(self):
        """Próbuje zainicjalizować moduł JarvisBrain na podstawie konfiguracji."""
        config = load_config()
        if config.get("api_key"):
            try:
                self.brain = JarvisBrain(config)
                self.log_message("[SYSTEM]: Silnik AI pomyślnie załadowany.")
            except Exception as e:
                self.log_message(f"[BŁĄD]: Błąd inicjalizacji silnika AI: {e}")
        else:
            self.log_message("[SYSTEM]: Ostrzeżenie - Brak klucza API. Przejdź do 'Ustawienia', aby skonfigurować aplikację.")

    def update_system_stats(self):
        """Pobiera i aktualizuje statystyki CPU i RAM."""
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        self.stats_label.configure(text=f"CPU: {cpu_usage}% | RAM: {ram_usage}%")
        # Wywołuj tę samą funkcję co 2000 ms (2 sekundy)
        self.after(2000, self.update_system_stats)

    def open_settings(self):
        """Otwiera okno z ustawieniami aplikacji."""
        SettingsWindow(self, on_save_callback=self.on_settings_saved)

    def on_settings_saved(self):
        """Callback po zapisaniu ustawień."""
        self.log_message("[SYSTEM]: Ustawienia zostały zaktualizowane.")
        self._init_brain()

    def toggle_sidebar(self):
        """Wysuwa/Chowa boczny panel akcji."""
        if self.sidebar_visible:
            self.sidebar_frame.grid_forget()
            self.sidebar_visible = False
        else:
            self.sidebar_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
            self.sidebar_visible = True

    def _refresh_sidebar(self):
        """Odświeża listę akcji ze złotej bazy z przyciskami (usuwanie/uruchamianie)."""
        # Wyczyszczenie dotychczasowych elementów panelu bocznego
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()

        for query, actions in self.knowledge_base.memory.items():
            btn_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=2)

            # Zastosowanie wraplength w celu łamania dłuższych linii tekstu, zamiast ich ucinania
            lbl = ctk.CTkLabel(btn_frame, text=query, width=130, wraplength=120, anchor="w", justify="left")
            lbl.pack(side="left", padx=5)

            # Przycisk gwiazdki symuluje kliknięcie/wywołanie danej ścieżki
            run_btn = ctk.CTkButton(btn_frame, text="★", width=30,
                                    command=lambda q=query: self._run_from_memory(q))
            run_btn.pack(side="right", padx=2)

    def _run_from_memory(self, query: str):
        """Uruchamia zadanie poleceniem wprost z bazy."""
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, query)
        self.execute_action()

    def _save_last_action(self):
        """Zapisuje ostatnie poprawnie wygenerowane akcje do bazy (Złota Lista)."""
        if self.last_query and self.last_actions:
            self.knowledge_base.add_learned_action(self.last_query, self.last_actions)
            self.log_message(f"[PAMIĘĆ]: Zapisano procedurę dla: '{self.last_query}'")
            self._refresh_sidebar()

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
        """Dodaje nową wiadomość do obszaru logów. Metoda ta jest thread-safe (używa self.after)."""
        def _append_log():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"{message}\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end") # Przewiń do samego dołu
        self.after(0, _append_log)

    def execute_action(self):
        """Metoda wywoływana po kliknięciu przycisku Wykonaj."""
        user_input = self.input_entry.get().strip()
        if not user_input:
            self.log_message("[SYSTEM]: Proszę wpisać komendę przed wykonaniem.")
            return

        if not self.brain:
            self.log_message("[BŁĄD]: Silnik AI nie jest gotowy. Uzupełnij klucz API w ustawieniach.")
            return

        self.log_message(f"[UŻYTKOWNIK]: {user_input}")
        self.input_entry.delete(0, "end")

        # Zablokowanie przycisku podczas wykonywania
        self.execute_button.configure(state="disabled")

        # Sprawdzanie pamięci "Złotej Listy"
        mem_actions = self.knowledge_base.get_action(user_input)
        if mem_actions:
            self.log_message("[JARVIS]: Używam zapamiętanej ścieżki.")
            # Wykonanie natychmiastowe z wątkiem dla płynności GUI
            threading.Thread(target=self._run_memory_thread, args=(mem_actions,), daemon=True).start()
            return

        # Uruchomienie zadania w nowym wątku, aby nie blokować GUI
        threading.Thread(target=self._process_command, args=(user_input,), daemon=True).start()

    def _run_memory_thread(self, actions):
        """Wykonywanie akcji ze złotej listy poza wątkiem głównym."""
        try:
            self._execute_actions(actions)
        finally:
            self.execute_button.configure(state="normal")

    def _process_command(self, user_input: str):
        """Wątek zajmujący się logiką przetwarzania przy użyciu AI z próbami (Autokorekta OCR) oraz "Wizją Selektywną" (ROI)."""
        try:
            target_window = ""
            global_offset_x = 0
            global_offset_y = 0

            # Pętla autokorekty (max 2 próby)
            for attempt in range(2):

                # Mechanizm "Wizji Selektywnej"
                screenshot = None
                if target_window:
                    self.log_message(f"[JARVIS] (Próba {attempt+1}/2): Pobieram wycinek z okna: '{target_window}'...")
                    screenshot, global_offset_x, global_offset_y = capture_window_roi(target_window)

                if not screenshot:
                    self.log_message(f"[JARVIS] (Próba {attempt+1}/2): Pobieram obraz z całego głównego ekranu...")
                    screenshot = capture_screen(scale_down=True)
                    global_offset_x, global_offset_y = 0, 0

                self.log_message("[JARVIS]: Wysyłam zapytanie do modelu sztucznej inteligencji...")
                response = self.brain.process_request(user_input, screenshot)

                thought = response.get("thought", "Brak przemyśleń.")
                plan = response.get("plan", [])
                actions = response.get("actions", [])

                # Zapisujemy zasugerowane przez AI docelowe okno dla kolejnych akcji (w tym autokorekty)
                suggested_target = response.get("target_window", "")
                if suggested_target:
                    target_window = suggested_target

                self.log_message(f"[JARVIS MYŚLI]: {thought}")
                if plan:
                    self.log_message(f"[JARVIS PLANUJE]: {', '.join(plan)}")

                if not actions:
                    self.log_message("[JARVIS]: Nie znaleziono żadnych akcji do wykonania.")
                    break
                else:
                    # Wykonanie akcji
                    self._execute_actions(actions, global_offset_x, global_offset_y)

                    # Logika Autokorekty i Weryfikacji (OCR) po wykonaniu akcji
                    has_error = False
                    if attempt == 0:
                        self.log_message("[JARVIS]: Weryfikuję rezultat zadania (OCR)...")

                        verification_screenshot = None
                        last_click_x, last_click_y = None, None

                        # Pobieramy koordynaty ostatniego kliknięcia, by zawęzić weryfikację
                        for act in reversed(actions):
                            if act.get("type") == "click":
                                last_click_x = act.get("x") + global_offset_x
                                last_click_y = act.get("y") + global_offset_y
                                break

                        if last_click_x is not None and last_click_y is not None:
                            verification_screenshot = capture_region(last_click_x, last_click_y)

                        # Jeśli OCR nie miał kliknięcia, weryfikuje pełny, wyostrzony ekran
                        if not verification_screenshot:
                            verification_screenshot = capture_screen(scale_down=False)

                        # Definicja potencjalnych komunikatów świadczących o porażce/błędzie (OCR)
                        error_keywords = ["błąd", "error", "nie znaleziono", "nie można", "nie udało się", "failed"]

                        for kw in error_keywords:
                            if is_text_visible(verification_screenshot, kw):
                                self.log_message(f"[AUTOKOREKTA]: Wykryto tekst '{kw}' na ekranie po wykonaniu akcji. Próbuję innej ścieżki...")
                                has_error = True
                                break

                        if has_error:
                            # Przechodzimy do kolejnej iteracji pętli (attempt = 1) bez dodawania do pamięci.
                            continue

                        # Brak błędów na ekranie przy pierwszej próbie.
                        self.log_message("[JARVIS]: Autokorekta nie wykryła błędów.")

                    self.log_message("[JARVIS]: Zadanie wykonane.")
                    self.last_query = user_input
                    self.last_actions = actions
                    # Gwiazdkę dodajemy do aktualnych zadań interfejsu
                    self.after(0, self._add_last_action_to_panel)
                    break

        except Exception as e:
            self.log_message(f"[BŁĄD WĄTKU]: {e}")
        finally:
            self.after(0, lambda: self.execute_button.configure(state="normal"))

    def _add_last_action_to_panel(self):
        """Dodaje przycisk szybkiego zapisu ostatniego zapytania."""
        self.log_message("[SYSTEM]: Możesz teraz zapisać tę komendę na stałe za pomocą przycisku [★ Zapisz Akcję].")
        # Jeśli istnieje już przycisk zapisujący, zaktualizuj go, albo utwórz nowy w stopce
        if not hasattr(self, 'save_action_button') or not self.save_action_button.winfo_exists():
            self.save_action_button = ctk.CTkButton(
                self.bottom_frame,
                text="★ Zapisz Akcję",
                fg_color="orange",
                hover_color="darkorange",
                command=self._save_last_action,
                width=120
            )
            self.save_action_button.grid(row=0, column=3, padx=(0, 10), pady=10)

    def _execute_actions(self, actions: list, offset_x: int = 0, offset_y: int = 0):
        """Sekwencyjnie wykonuje zlecone przez silnik akcje, uwzględniając offset "Wizji Selektywnej" (ROI)."""
        for act in actions:
            action_type = act.get("type")

            if action_type == "click":
                local_x = act.get("x")
                local_y = act.get("y")

                # Przeliczenie na współrzędne globalne monitora
                global_x = local_x + offset_x
                global_y = local_y + offset_y

                self.log_message(f"[JARVIS AKCJA]: Klikam w punkt ({global_x}, {global_y})")
                try:
                    click_at(global_x, global_y)
                except Exception as e:
                    self.log_message(f"[BŁĄD AKCJI]: Nie udało się kliknąć - {e}")

            elif action_type == "type":
                text = act.get("text", "")
                self.log_message(f"[JARVIS AKCJA]: Wpisuję tekst: '{text}'")
                try:
                    type_text(text)
                except Exception as e:
                    self.log_message(f"[BŁĄD AKCJI]: Nie udało się wpisać tekstu - {e}")

            elif action_type == "press":
                key = act.get("key", "")
                self.log_message(f"[JARVIS AKCJA]: Naciskam klawisz '{key}'")
                try:
                    press_key(key)
                except Exception as e:
                    self.log_message(f"[BŁĄD AKCJI]: Nie udało się wcisnąć klawisza - {e}")

            elif action_type == "run_app":
                query = act.get("query", "")
                self.log_message(f"[JARVIS AKCJA]: Szukam aplikacji: '{query}'")
                app_path = self.app_scanner.find_app(query)

                if app_path:
                    try:
                        self.log_message(f"[JARVIS AKCJA]: Uruchamiam zlokalizowaną ścieżkę: '{app_path}'")
                        # Używamy Popen bez shell=True dla bezpieczeństwa, jeśli to jawna ścieżka.
                        subprocess.Popen(app_path)
                    except Exception as e:
                        self.log_message(f"[BŁĄD AKCJI]: Nie udało się uruchomić procesu - {e}")
                else:
                    self.log_message(f"[JARVIS OSTRZEŻENIE]: Nie potrafię zlokalizować programu dla zapytania: '{query}'.")

            elif action_type == "clipboard_write":
                text = act.get("text", "")
                self.log_message("[JARVIS AKCJA]: Kopiuję dane do schowka")
                try:
                    copy_to_clipboard(text)
                except Exception as e:
                    self.log_message(f"[BŁĄD AKCJI]: Nie udało się skopiować - {e}")

            elif action_type == "log_result":
                text = act.get("text", "")
                self.log_message(f"[JARVIS WYNIK]: {text}")

            else:
                self.log_message(f"[OSTRZEŻENIE]: Nierozpoznana akcja: {act}")

    def stop_action(self):
        """Metoda wywoływana po kliknięciu przycisku Zatrzymaj."""
        self.log_message("[SYSTEM]: Zatrzymywanie aktualnych procesów agenta...")
        self.status_label.configure(text="Stan: Zatrzymany")
