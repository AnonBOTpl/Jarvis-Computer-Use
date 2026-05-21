import subprocess
import winreg
import shutil
import json
import time
import logging
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

class AppScanner:
    """Moduł odpowiedzialny za wyszukiwanie aplikacji w systemie operacyjnym Windows."""

    CACHE_DURATION = 60

    def __init__(self):
        self.known_apps = {}
        self._cache_time = 0
        self.synonyms = {
            "notatnik": "notepad",
            "kalkulator": "calc",
            "przeglądarka": "chrome",
            "cmd": "cmd",
            "wiersz poleceń": "cmd",
            "powershell": "powershell",
            "wordpad": "wordpad",
            "paint": "mspaint"
        }

    def refresh_apps(self):
        """Aktualizuje listę znanych aplikacji ze wszystkich źródeł."""
        now = time.time()
        if now - self._cache_time < self.CACHE_DURATION:
            return

        self.known_apps.clear()
        self._scan_start_menu()
        self._scan_registry()
        self._cache_time = time.time()

    def _scan_start_menu(self):
        """Skanuje aplikacje w menu Start za pomocą PowerShell'a (Get-StartApps)."""
        try:
            cmd = ['powershell', '-Command', "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode != 0 or not result.stdout.strip():
                logger.warning("Get-StartApps nie zwrócił danych.")
                return

            apps_data = json.loads(result.stdout)

            if isinstance(apps_data, dict):
                apps_data = [apps_data]

            for app in apps_data:
                name = app.get('Name')
                appid = app.get('AppID')
                if name and appid:
                    self.known_apps[name.lower()] = appid
        except json.JSONDecodeError as e:
            logger.error(f"Błąd parsowania JSON z Get-StartApps: {e}")
        except Exception as e:
            logger.error(f"Błąd podczas skanowania Start Menu: {e}")

    def _scan_registry(self):
        """Skanuje ścieżki instalacyjne popularnych programów za pomocą rejestru systemowego."""
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]

        for hkey, reg_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, reg_path) as key:
                    sub_key_count = winreg.QueryInfoKey(key)[0]
                    for i in range(sub_key_count):
                        try:
                            sub_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_key_name) as sub_key:
                                try:
                                    app_path, _ = winreg.QueryValueEx(sub_key, "")
                                    app_name = sub_key_name.lower().replace(".exe", "")
                                    self.known_apps[app_name] = app_path
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except FileNotFoundError:
                continue

    def _launch_aumid(self, appid: str):
        """Uruchamia aplikację przez AUMID (AppUserModelID) z wykorzystaniem shell:AppsFolder."""
        try:
            subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{appid}"])
            return True
        except Exception as e:
            logger.error(f"Nie można uruchomić AUMID {appid}: {e}")
            return False

    def find_app(self, query_name: str):
        """
        Wyszukuje pożądaną aplikację na podstawie nazwy, używając:
        1. Słownika synonimów.
        2. Narzędzia 'shutil.which' (sprawdzanie w zmiennych PATH środowiska).
        3. RapidFuzz do dopasowania względem 'known_apps'.

        Zwraca:
            Pełną ścieżkę do programu (plik .exe), czystą komendę systemową
            albo None, jeśli aplikacja nie została znaleziona.
        """
        query_lower = query_name.lower().strip()
        if not query_lower:
            return None

        if query_lower in self.synonyms:
            query_lower = self.synonyms[query_lower]

        path_result = shutil.which(query_lower)
        if path_result:
            return path_result

        self.refresh_apps()

        if not self.known_apps:
            return None

        choices = list(self.known_apps.keys())
        result = process.extractOne(query_lower, choices, scorer=fuzz.partial_ratio)

        if result:
            best_match, score, _ = result
            if score >= 70:
                match_path = self.known_apps[best_match]

                if match_path.startswith("search:query="):
                    logger.info(f"Aplikacja {query_name} to wyszukiwanie, pomijam.")
                    return None

                if "!" in match_path:
                    logger.info(f"Aplikacja {query_name} ma AUMID, używam shell:AppsFolder.")
                    return ("aumid", match_path)

                return match_path

        return None
