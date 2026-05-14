import json
import os
import customtkinter as ctk
from google import genai

CONFIG_FILE = "config.json"

def load_config():
    """Wczytuje konfigurację z pliku JSON. Zwraca domyślne wartości jeśli plik nie istnieje."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd wczytywania konfiguracji: {e}")
    return {"api_key": "", "model_name": ""}

def save_config(config):
    """Zapisuje konfigurację do pliku JSON."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

class SettingsWindow(ctk.CTkToplevel):
    """Okno ustawień, pozwalające na wpisanie klucza API i wybór modelu."""
    def __init__(self, master, on_save_callback=None):
        super().__init__(master)
        self.title("Ustawienia - Jarvis")
        self.geometry("450x300")
        self.on_save_callback = on_save_callback

        # Okno modalne (zawsze na wierzchu i blokuje interakcję z głównym oknem)
        self.grab_set()
        self.attributes("-topmost", True)

        self.config = load_config()

        # --- Klucz API ---
        self.api_key_label = ctk.CTkLabel(self, text="Klucz API (Google Gemini):", font=ctk.CTkFont(weight="bold"))
        self.api_key_label.pack(padx=20, pady=(20, 5), anchor="w")

        self.api_key_entry = ctk.CTkEntry(self, width=400, show="*")
        self.api_key_entry.pack(padx=20, pady=5)
        self.api_key_entry.insert(0, self.config.get("api_key", ""))

        # --- Pobieranie modeli ---
        self.fetch_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fetch_frame.pack(padx=20, pady=10, fill="x")

        self.fetch_button = ctk.CTkButton(self.fetch_frame, text="Pobierz modele", command=self.fetch_models, width=120)
        self.fetch_button.pack(side="left", padx=(0, 10))

        self.status_label = ctk.CTkLabel(self.fetch_frame, text="", text_color="red")
        self.status_label.pack(side="left")

        # --- Wybór modelu ---
        self.model_label = ctk.CTkLabel(self, text="Wybierz model:", font=ctk.CTkFont(weight="bold"))
        self.model_label.pack(padx=20, pady=(10, 5), anchor="w")

        default_model = self.config.get("model_name", "Brak pobranych modeli")
        if not default_model:
            default_model = "Brak pobranych modeli"

        self.model_var = ctk.StringVar(value=default_model)
        self.model_optionmenu = ctk.CTkOptionMenu(self, variable=self.model_var, values=[default_model], width=400)
        self.model_optionmenu.pack(padx=20, pady=5)

        # --- Zapis ---
        self.save_button = ctk.CTkButton(self, text="Zapisz ustawienia", command=self.save_settings, width=150)
        self.save_button.pack(padx=20, pady=20)

    def fetch_models(self):
        """Pobiera listę modeli z Google Gemini API na podstawie wprowadzonego klucza."""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.status_label.configure(text="Podaj klucz API!", text_color="red")
            return

        self.status_label.configure(text="Pobieranie...", text_color="orange")
        self.update_idletasks()

        try:
            # Tworzenie klienta z podanym kluczem
            client = genai.Client(api_key=api_key)
            models_response = client.models.list()

            # Zbieranie nazw modeli zawierających 'gemini'
            model_names = []
            for m in models_response:
                if hasattr(m, 'name') and "gemini" in m.name.lower():
                    # Format nazwy zależy od odpowiedzi (zwykle np. models/gemini-2.5-flash)
                    name = m.name.replace("models/", "") if m.name.startswith("models/") else m.name
                    model_names.append(name)

            if not model_names:
                # Opcja awaryjna
                model_names = ["gemini-2.5-flash", "gemini-2.5-pro"]

            self.model_optionmenu.configure(values=model_names)

            # Próba ustawienia wcześniej wybranego modelu
            saved_model = self.config.get("model_name")
            if saved_model in model_names:
                self.model_var.set(saved_model)
            else:
                self.model_var.set(model_names[0])

            self.status_label.configure(text="Sukces", text_color="green")

        except Exception as e:
            self.status_label.configure(text="Błąd autoryzacji", text_color="red")
            print(f"Błąd podczas pobierania modeli: {e}")
            # Tryb awaryjny - zezwalajmy na ręczny wybór najpopularniejszych w wypadku błędu
            self.model_optionmenu.configure(values=["gemini-2.5-flash", "gemini-2.5-pro"])
            self.model_var.set("gemini-2.5-flash")

    def save_settings(self):
        """Zapisuje dane do json i wywołuje callback w głównym oknie."""
        new_config = {
            "api_key": self.api_key_entry.get().strip(),
            "model_name": self.model_var.get()
        }
        save_config(new_config)
        if self.on_save_callback:
            self.on_save_callback()
        self.destroy()
