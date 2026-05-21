import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Jestes inteligentnym asystentem i deweloperem sterujacym komputerem (Jarvis).
Twoim glownym narzedziem rozwiazywania problemow jest KOD (Python, PowerShell).
NIE widzisz ekranu komputera. Polegasz na pisaniu kodow i symulowaniu myszy/klawiatury.

ZASADY:
1. Jesli prosze o stworzenie pliku, analize danych systemowych, wygenerowanie raportu - UZYJ KODU.
2. Planuj zlozone operacje poprzez przyslenie lancucha krokow.
3. Mozesz zwrocic JEDNA liste operacji. Jesli wybierzesz skrypt, zwroc tylko 1 akcje "run_code".
4. Przed wpisaniem tekstu w oknie, kliknij w to okno, aby je aktywowac.

Zwroc odpowiedz WYLACZNIE w formacie JSON:
{
    "thought": "Twoje przyslenia (po polsku).",
    "plan": ["krok 1", "krok 2"],
    "actions": [
        {"type": "click", "x": 100, "y": 200},
        {"type": "type", "text": "przykladowy tekst"},
        {"type": "press", "key": "enter"},
        {"type": "run_app", "query": "notatnik"},
        {"type": "run_code", "language": "python", "code": "print('witaj')"},
        {"type": "log_result", "text": "Wynik operacji"}
    ]
}
Jesli nie wiesz co zrobic, zwroc pusta liste akcji z wyjasnieniem w 'thought'.
"""


class LocalBrain:
    def __init__(self, config: dict):
        self.model = config.get("local_model", "qwen2.5:3b")
        base_url = config.get("ollama_url", "http://localhost:11434")
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
        self._test_connection()

    def _test_connection(self):
        try:
            self.client.models.list()
            logger.info(f"Polaczono z Ollama. Model: {self.model}")
        except Exception as e:
            logger.warning(f"Nie mozna polaczyc sie z Ollama: {e}")
            raise ConnectionError(
                f"Nie mozna polaczyc sie z Ollama na {self.client.base_url}. "
                f"Upewnij sie ze Ollama jest uruchomiona."
            )

    def process_request(self, user_prompt: str, screenshot=None) -> dict:
        if screenshot is not None:
            logger.info("LocalBrain: pomijam obraz - model nie wspiera wizji.")

        prompt = f"{SYSTEM_INSTRUCTION}\n\nInstrukcja uzytkownika: {user_prompt}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
                timeout=120
            )

            raw = response.choices[0].message.content
            result = json.loads(raw)

            if "actions" not in result:
                result["actions"] = []
            if "thought" not in result:
                result["thought"] = ""
            if "plan" not in result:
                result["plan"] = []

            return result

        except json.JSONDecodeError:
            logger.error("LocalBrain: blad parsowania JSON z modelu.")
            return {"thought": "Blad parsowania odpowiedzi modelu.", "actions": []}
        except Exception as e:
            logger.error(f"LocalBrain: blad zapytania: {e}")
            return {"thought": f"Blad: {e}", "actions": []}
