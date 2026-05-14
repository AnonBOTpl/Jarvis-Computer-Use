import json
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

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
        Twoim zadaniem jest zanalizować dostarczony zrzut ekranu i instrukcję od użytkownika,
        a następnie zdecydować jakie akcje (mysz, klawiatura) muszą zostać wykonane.

        Zwróć odpowiedź WYŁĄCZNIE w formacie JSON o następującej strukturze:
        {
            "thought": "Twoje przemyślenia na temat tego, co widzisz i co zamierzasz zrobić (w języku polskim).",
            "actions": [
                {"type": "click", "x": 100, "y": 200},
                {"type": "type", "text": "przykładowy tekst"},
                {"type": "press", "key": "enter"},
                {"type": "run_app", "query": "nazwa_programu"}
            ]
        }
        Jeśli nie wiesz co zrobić lub nie potrafisz zlokalizować żądanego elementu na ekranie, zwróć pustą listę akcji z odpowiednim komentarzem w 'thought'.
        """

        prompt = f"Instrukcja użytkownika: {user_prompt}"

        # Inicjowanie konfiguracji z instrukcją systemową oraz wymuszeniem zwracania popranwego formatu JSON
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.2
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[screenshot, prompt],
                config=config
            )

            # Parsowanie zwróconego JSONa z odpowiedzi
            result = json.loads(response.text)
            return result

        except json.JSONDecodeError:
            print("Błąd parsowania JSON z odpowiedzi modelu.")
            return {"thought": "Zwrócono nieprawidłowy format od modelu.", "actions": []}
        except Exception as e:
            print(f"Błąd podczas komunikacji z API Gemini: {e}")
            return {"thought": f"Błąd wewnętrzny: {e}", "actions": []}
