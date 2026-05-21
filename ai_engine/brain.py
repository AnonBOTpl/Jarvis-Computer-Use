import json
import base64
import logging
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class JarvisBrain:
    """Moduł odpowiedzialny za przetwarzanie informacji i podejmowanie decyzji przy użyciu Google Gemini."""

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.model_name = config.get("model_name", "gemini-2.5-pro")

        if not self.api_key:
            raise ValueError("Brak klucza API. Skonfiguruj ustawienia.")

        self.client = genai.Client(api_key=self.api_key)

    def _image_to_base64(self, img: Image.Image) -> str:
        """Konwertuje obiekt PIL Image do base64 dla API Gemini."""
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def process_request(self, user_prompt: str, screenshot: Image.Image) -> dict:
        """
        Wysyła zrzut ekranu oraz żądanie użytkownika do modelu AI z prośbą o wygenerowanie akcji.
        Zwraca odpowiedź w postaci słownika z wyciągniętymi akcjami.
        """

        system_instruction = """
        Jesteś inteligentnym asystentem sterującym komputerem (Jarvis).
        Twoim głównym narzędziem jest KOD (Python, PowerShell).
        Widzisz ekran TYLKO gdy użyjesz "request_vision", inaczej NIE widzisz pulpitu.

        ZASADY:
        1. Do tworzenia folderów, plików, analizy systemu, edycji - UŻYJ KODU przez "run_code".
        2. Dla powitań i prostych rozmów - użyj {"type": "log_result", "text": "..."}.
        3. GUI (click, type, press) używaj TYLKO do fizycznej interakcji z oknami aplikacji.
        4. Do otwierania aplikacji użyj "run_app".
        5. ZAWSZE generuj przynajmniej jedną akcję dla konkretnego zadania.
        6. Zawsze używaj kodowania utf-8 w kodzie (open(..., encoding='utf-8')).

        Przykłady:
        - Powitanie: [{"type": "log_result", "text": "Cześć! Jak mogę pomóc?"}]
        - Utwórz folder: [{"type": "run_code", "language": "python", "code": "import os\nos.makedirs('ścieżka', exist_ok=True)"}]
        - Otwórz notatnik: [{"type": "run_app", "query": "notepad"}]
        - Kliknij i wpisz: [{"type": "click", "x": 100, "y": 200}, {"type": "type", "text": "hello"}]

        Zwróć odpowiedź WYŁĄCZNIE w formacie JSON:
        {
            "thought": "Twoje przemyślenia po polsku.",
            "target_window": "tytuł okna lub pusty",
            "plan": ["krok 1", "krok 2"],
            "actions": [lista akcji - nigdy pusta dla konkretnego zadania]
        }
        Jeśli nie wiesz co zrobić, zwróć pustą listę akcji z wyjaśnieniem w 'thought'.
        """

        prompt = f"Instrukcja użytkownika: {user_prompt}"

        # Jeśli nie przesyłamy zrzutu ekranu (np. tryb autonaprawy kodu)
        contents = [prompt]
        if screenshot:
            contents = [screenshot, prompt]

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.2
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            # Parsowanie zwróconego JSONa z odpowiedzi
            result = json.loads(response.text)

            # Dodanie metadanych odnośnie tokenów
            if hasattr(response, 'usage_metadata'):
                result["usage_metadata"] = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count
                }

            # Walidacja odpowiedzi AI
            if not isinstance(result, dict):
                logger.warning("AI zwróciło nie-słownikową odpowiedź, resetuję.")
                return {"thought": "Nieprawidłowy format odpowiedzi.", "actions": []}

            if "actions" not in result:
                result["actions"] = []
            if "thought" not in result:
                result["thought"] = "Brak przemyśleń."
            if "plan" not in result:
                result["plan"] = []

            return result

        except json.JSONDecodeError:
            print("Błąd parsowania JSON z odpowiedzi modelu.")
            return {"thought": "Zwrócono nieprawidłowy format od modelu.", "actions": []}
        except Exception as e:
            print(f"Błąd podczas komunikacji z API Gemini: {e}")
            return {"thought": f"Błąd wewnętrzny: {e}", "actions": []}
