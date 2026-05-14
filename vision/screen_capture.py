import mss
from PIL import Image

def capture_screen() -> Image.Image:
    """
    Przechwytuje obraz całego głównego ekranu i zwraca go jako obiekt PIL Image.
    Zwraca obraz w formacie RGB.
    """
    with mss.mss() as sct:
        # Przechwytuje główny monitor (1)
        monitor = sct.monitors[1]
        screenshot_bgra = sct.grab(monitor)

        # Konwersja obrazu z formatu BGRA, używanego domyślnie przez mss, do RGB
        img = Image.frombytes("RGB", screenshot_bgra.size, screenshot_bgra.bgra, "raw", "BGRX")
        return img
