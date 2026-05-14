import subprocess
import winreg
import shutil
from rapidfuzz import process, fuzz

class AppScanner:
    """Moduł odpowiedzialny za wyszukiwanie aplikacji w systemie operacyjnym Windows."""

    def __init__(self):
        self.known_apps = {}
        self.refresh_apps()

    def refresh_apps(self):
        """Aktualizuje listę znanych aplikacji ze wszystkich źródeł."""
        self.known_apps.clear()
        self._scan_start_menu()
        self._scan_registry()

    def _scan_start_menu(self):
        """Skanuje aplikacje w menu Start za pomocą PowerShell'a (Get-StartApps)."""
        try:
            # Użycie powershell do pobrania nazwy i AppID (często zawiera ścieżkę dla programów win32)
            cmd = ['powershell', '-Command', "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                import json
                apps_data = json.loads(result.stdout)
                for app in apps_data:
                    name = app.get('Name')
                    appid = app.get('AppID')
                    if name and appid:
                        # W przypadku AppID nie zawsze jest to bezpośrednia ścieżka do .exe,
                        # ale zachowujemy ją w celach identyfikacyjnych dla ShellExecute.
                        self.known_apps[name.lower()] = appid
        except Exception as e:
            print(f"Błąd podczas skanowania Start Menu: {e}")

    def _scan_registry(self):
        """Skanuje ścieżki instalacyjne popularnych programów za pomocą rejestru systemowego."""
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]

        for hkey, reg_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, reg_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_key_name) as sub_key:
                                try:
                                    app_path, _ = winreg.QueryValueEx(sub_key, "")
                                    # Pobranie samej nazwy exeka bez rozszerzenia .exe
                                    app_name = sub_key_name.lower().replace(".exe", "")
                                    self.known_apps[app_name] = app_path
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except FileNotFoundError:
                continue

    def find_app(self, query_name: str) -> str:
        """
        Wyszukuje pożądaną aplikację na podstawie nazwy, używając:
        1. Narzędzia 'shutil.which' (sprawdzanie w zmiennych PATH środowiska).
        2. RapidFuzz do dopasowania względem 'known_apps'.

        Zwraca:
            Pełną ścieżkę do programu, AppID (do użytku jako shell komenda)
            lub po prostu oryginalne query w przypadku nieznalezienia.
        """
        query_lower = query_name.lower().strip()

        # 1. Sprawdzenie czy aplikacja znajduje się w zmiennej PATH (np. 'notepad', 'calc')
        path_result = shutil.which(query_lower)
        if path_result:
            return path_result

        # 2. Przeszukiwanie przy pomocy fuzzy matching (RapidFuzz) z known_apps
        if not self.known_apps:
            self.refresh_apps()

        choices = list(self.known_apps.keys())
        if choices:
            # Użycie partial_ratio pozwala na lepsze radzenie sobie z zapytaniami
            # takimi jak "chrome" w odniesieniu do "google chrome".
            result = process.extractOne(query_lower, choices, scorer=fuzz.partial_ratio)

            if result:
                best_match, score, index = result
                # Przyjęto minimalny próg pewności (np. 70%)
                if score >= 70:
                    return self.known_apps[best_match]

        return query_name # Jeżeli nie zdołano znaleźć pasującej ścieżki, zwraca domyślne hasło
