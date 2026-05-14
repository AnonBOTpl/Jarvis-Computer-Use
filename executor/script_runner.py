import subprocess
import os
import sys
import threading
import queue

class ScriptRunner:
    """Moduł odpowiedzialny za izolowane, asynchroniczne uruchamianie kodu Python lub PowerShell."""

    def __init__(self, output_callback=None, error_callback=None, finished_callback=None):
        self.output_callback = output_callback
        self.error_callback = error_callback
        self.finished_callback = finished_callback
        # Zapewnia uruchomienie interpretera we wskazanym .venv w którym działa główny proces
        self.python_exec = sys.executable
        self._current_process = None

    def run_python_code(self, code: str):
        """Uruchamia podany kod języka Python w wirtualnym środowisku agenta."""
        # Zapis do tymczasowego pliku
        script_path = "temp_agent_script.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        cmd = [self.python_exec, script_path]
        self._execute_async(cmd, is_powershell=False, temp_file=script_path)

    def run_powershell_code(self, code: str):
        """Uruchamia podany kod za pomocą systemowego interpretera PowerShell."""
        cmd = ["powershell", "-Command", code]
        self._execute_async(cmd, is_powershell=True)

    def stop_execution(self):
        """Wymusza zamknięcie pracującego skryptu."""
        if self._current_process and self._current_process.poll() is None:
            self._current_process.terminate()
            if self.error_callback:
                self.error_callback("[ZATRZYMANO] Wykonywanie skryptu przerwane przez użytkownika.")

    def _execute_async(self, cmd: list, is_powershell: bool = False, temp_file: str = None):
        """Realizuje asynchroniczne odczytywanie strumienia danych wyjściowych z wbudowanego polecenia."""
        def target():
            try:
                # W przypadku PowerShell mogą wystąpić problemy z polskimi znakami, stąd kodowanie okna cmd na 65001 w run_jarvis
                encoding = "utf-8" if not is_powershell else "cp852"

                self._current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding=encoding,
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                # Wątki pomocnicze do logowania na bieżąco
                # Przechowywanie zrzutu pełnego błędu stderr, by potem nakarmić nim asystenta AI do pętli Autonaprawy
                captured_stderr = []

                def read_stdout(stream, callback):
                    for line in iter(stream.readline, ''):
                        if line and callback:
                            callback(line.strip())
                    stream.close()

                def read_stderr(stream, callback, buffer):
                    for line in iter(stream.readline, ''):
                        if line:
                            buffer.append(line.strip())
                            if callback:
                                callback(line.strip())
                    stream.close()

                stdout_thread = threading.Thread(target=read_stdout, args=(self._current_process.stdout, self.output_callback), daemon=True)
                stderr_thread = threading.Thread(target=read_stderr, args=(self._current_process.stderr, self.error_callback, captured_stderr), daemon=True)

                stdout_thread.start()
                stderr_thread.start()

                self._current_process.wait()
                stdout_thread.join()
                stderr_thread.join()

                return_code = self._current_process.returncode
                final_stderr_str = "\n".join(captured_stderr)

            except Exception as e:
                err_msg = f"[BŁĄD KRYTYCZNY RUNNERA]: {e}"
                if self.error_callback:
                    self.error_callback(err_msg)
                return_code = -1
                final_stderr_str = err_msg
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                if self.finished_callback:
                    self.finished_callback(return_code, final_stderr_str)

        threading.Thread(target=target, daemon=True).start()
