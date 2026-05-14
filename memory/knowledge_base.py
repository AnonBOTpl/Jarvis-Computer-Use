import json
import os

KNOWLEDGE_FILE = "knowledge.json"

class KnowledgeBase:
    """Moduł odpowiedzialny za 'Złotą Listę' pamięci akcji. Oszczędza tokeny API poprzez zapis lokalnych poleceń."""

    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        """Wczytuje z pliku JSON strukturę pamięci (Słownik: {komenda: [lista_akcji]})."""
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Błąd odczytu bazy wiedzy: {e}")
        return {}

    def _save_memory(self):
        """Zapisuje bieżący stan pamięci do pliku."""
        try:
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu bazy wiedzy: {e}")

    def add_learned_action(self, query: str, actions: list):
        """Dodaje zsekwencjonowaną akcję przypisaną do konkretnej komendy użytkownika."""
        query_lower = query.lower().strip()
        self.memory[query_lower] = actions
        self._save_memory()

    def get_action(self, query: str):
        """Zwraca listę akcji, jeśli dana komenda jest zapisana w pamięci. Zwraca None, jeśli komendy brakuje."""
        query_lower = query.lower().strip()
        return self.memory.get(query_lower)

    def remove_action(self, query: str):
        """Usuwa zapisaną akcję z pamięci."""
        query_lower = query.lower().strip()
        if query_lower in self.memory:
            del self.memory[query_lower]
            self._save_memory()
