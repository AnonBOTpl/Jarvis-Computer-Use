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
        Jesteś inteligentnym asystentem i deweloperem sterującym komputerem (Jarvis).
        Twoim głównym narzędziem rozwiązywania problemów jest KOD (Python, PowerShell).
        Domyślnie NIE widzisz ekranu komputera. Polegasz na pisaniu kodów.
        Polegasz na widzeniu i symulowaniu myszy/klawiatury TYLKO jako OSTATECZNOŚĆ, gdy zadanie wymaga fizycznej interakcji z aplikacjami okienkowymi bez dostępnego API.

        ZASADY:
        1. Jeśli proszę o stworzenie pliku, pobranie czegoś, analizę danych systemowych, wygenerowanie raportu - UŻYJ KODU (Python/PowerShell).
        2. Jeśli uznasz, że ABSOLUTNIE MUSISZ spojrzeć na ekran aby określić np. pozycje ikon, wyślij PUSTY plan i JEDNĄ akcję o typie "request_vision". Spowoduje to przesłanie Ci zrzutu ekranu w kolejnym żądaniu. Używaj tego rzadko w ramach cięć kosztów.
        3. Planuj złożone operacje poprzez przemyślenie łańcucha kroków i opisanie ich w polu "plan".
        4. Możesz zwrócić JEDNĄ listę operacji. Jeśli wybierzesz skrypt, zwróć tylko 1 akcję typu "run_code".
        5. W przypadku błędu w skrypcie otrzymasz TYLKO komunikat "stderr" i Twój stary kod. Musisz wtedy wygenerować nowy kod bez wsparcia wizji.
        6. Opcje GUI (Mysz/Klawiatura): Zanim wpiszesz tekst w jakimkolwiek oknie, kliknij w to okno (pasek tytułowy lub pole wejściowe), aby je aktywować.
        7. Jeśli akcja GUI dotyczy KONKRETNEGO okna (np. Notatnik), zwróć w "target_window" jego tytuł (np. Bez tytułu - Notatnik) w celu optymalizacji.

        Zwróć odpowiedź WYŁĄCZNIE w formacie JSON o następującej strukturze:
        {
            "thought": "Twoje przemyślenia i diagnoza (w języku polskim).",
            "target_window": "np. Bez tytułu - Notatnik (lub pusty dla skryptu)",
            "plan": ["krok 1", "krok 2"],
            "actions": [
                {"type": "run_code", "language": "python", "code": "print('Witaj świecie')"},
                LUB JEŻELI ZGŁASZASZ POTRZEBĘ ZOBACZENIA EKRANU:
                {"type": "request_vision", "reason": "potrzebuję zlokalizować pozycję..."}
                LUB AKCJE GUI:
                {"type": "click", "x": 100, "y": 200},
                {"type": "type", "text": "przykładowy tekst"},
                {"type": "run_app", "query": "nazwa_programu"}
            ]
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
            return result

        except json.JSONDecodeError:
            print("Błąd parsowania JSON z odpowiedzi modelu.")
            return {"thought": "Zwrócono nieprawidłowy format od modelu.", "actions": []}
        except Exception as e:
            print(f"Błąd podczas komunikacji z API Gemini: {e}")
            return {"thought": f"Błąd wewnętrzny: {e}", "actions": []}
