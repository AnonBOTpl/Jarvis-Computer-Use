import json
import logging
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Jestes inteligentnym asystentem sterujacym komputerem (Jarvis).
Dzialasz wylacznie przez generowanie akcji w formacie JSON.

WAZNE ZASADY:
1. Preferowanym narzedziem jest KOD Python przez akcje "run_code".
2. Do tworzenia folderow, plikow, analizy systemu, pobierania danych - ZAWSZE uzywaj run_code.
3. Nie probuj uzywac klikniec/typowania do operacji na systemie plikow.
4. Dla prostych powitan lub rozmowy - uzyj "log_result".
5. ZAWSZE zwracaj liste akcji. Pusta lista to ostatecznosc (gdy zadanie niemozliwe).

Przyklady akcji:
- Powitanie: {"type": "log_result", "text": "Czesc! Jak moge pomoc?"}
- Utworz folder: {"type": "run_code", "language": "python", "code": "import os\nos.makedirs('C:/Users/Admin/Desktop/test', exist_ok=True)"}
- UWAGA: W sciezkach Windows uzywaj forward slash (C:/Users/...) zamiast backslashy.
- Otworz notatnik: {"type": "run_app", "query": "notepad"}
- Kliknij: {"type": "click", "x": 500, "y": 300}
- Wpisz tekst: {"type": "type", "text": "przykladowy tekst"}
- Wcisnij klawisz: {"type": "press", "key": "enter"}

Zwroc odpowiedz WYLACZNIE jako JSON:
{
    "thought": "Twoje przyslenia po polsku.",
    "plan": ["krok 1", "krok 2"],
    "actions": [
        {"type": "run_code", "language": "python", "code": "# kod pythona"},
        {"type": "log_result", "text": "Gotowe."}
    ]
}
"""


class LocalBrain:
    def __init__(self, config: dict):
        self.model = config.get("local_model", "qwen2.5:3b")
        self.num_ctx = config.get("num_ctx", 4096)
        base_url = config.get("ollama_url", "http://localhost:11434")
        self.base_url = base_url.rstrip("/")
        self.client = OpenAI(base_url=f"{self.base_url}/v1", api_key="ollama")
        self._test_connection()

    def cleanup(self):
        """Zwalnia model z GPU po zamknieciu."""
        try:
            requests.post(f"{self.base_url}/api/generate",
                          json={"model": self.model, "keep_alive": 0},
                          timeout=5)
            logger.info(f"Model {self.model} zwolniony z pamieci GPU.")
        except Exception as e:
            logger.warning(f"Nie udalo sie zwolnic modelu z GPU: {e}")

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
                timeout=120,
                extra_body={"num_ctx": self.num_ctx}
            )

            raw = response.choices[0].message.content
            result = json.loads(raw)

            if "actions" not in result:
                result["actions"] = []
            if "thought" not in result:
                result["thought"] = ""
            if "plan" not in result:
                result["plan"] = []

            if response.usage:
                result["usage_metadata"] = {
                    "prompt_token_count": response.usage.prompt_tokens,
                    "candidates_token_count": response.usage.completion_tokens,
                    "total_token_count": response.usage.total_tokens,
                }

            return result

        except json.JSONDecodeError:
            logger.error("LocalBrain: blad parsowania JSON z modelu.")
            return {"thought": "Blad parsowania odpowiedzi modelu.", "actions": []}
        except Exception as e:
            logger.error(f"LocalBrain: blad zapytania: {e}")
            return {"thought": f"Blad: {e}", "actions": []}
