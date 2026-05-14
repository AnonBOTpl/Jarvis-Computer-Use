import pyautogui

# Zabezpieczenie przed utratą kontroli nad urządzeniem (Fail-Safe).
# Przesunięcie myszy w róg ekranu przerwie działanie pyautogui.
pyautogui.FAILSAFE = True

def click_at(x: int, y: int, button: str = 'left'):
    """
    Przesuwa kursor myszy na wskazane współrzędne (x, y) i wykonuje kliknięcie.
    """
    pyautogui.moveTo(x, y, duration=0.25)
    pyautogui.click(button=button)

def type_text(text: str, interval: float = 0.05):
    """
    Wpisuje podany tekst z symulowanym opóźnieniem pomiędzy znakami (dla naturalniejszego efektu).
    """
    pyautogui.write(text, interval=interval)

def press_key(key: str):
    """
    Naciska i zwalnia pojedynczy klawisz na klawiaturze (np. 'enter', 'tab', 'esc').
    """
    pyautogui.press(key)

import pyperclip
import time

def copy_to_clipboard(text: str):
    """Kopiuje podany tekst do systemowego schowka (z opóźnieniem do prawidłowej interakcji)."""
    time.sleep(0.5)
    pyperclip.copy(text)

def get_from_clipboard() -> str:
    """Zwraca zawartość systemowego schowka."""
    return pyperclip.paste()
