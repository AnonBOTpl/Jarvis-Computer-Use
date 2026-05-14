import mss
import pygetwindow as gw
from PIL import Image

def capture_screen(scale_down: bool = True, target_width: int = 1280) -> Image.Image:
    """
    Przechwytuje obraz całego głównego ekranu.
    Opcjonalnie skaluje w dół oraz konwertuje do skali szarości, aby
    zoptymalizować wielkość pliku/tokenów wysyłanych do API Gemini.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot_bgra = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot_bgra.size, screenshot_bgra.bgra, "raw", "BGRX")

        if scale_down:
            # Zachowanie proporcji ekranu
            ratio = target_width / float(img.size[0])
            target_height = int((float(img.size[1]) * float(ratio)))
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            # Konwersja do skali szarości minimalizuje rozmiar
            img = img.convert("L")

        return img

def capture_window_roi(window_title_keyword: str):
    """
    Znajduje pierwsze okno zawierające 'window_title_keyword' w tytule.
    Zwraca wycinek (ROI) tego okna jako obraz oraz jego koordynaty (offset_x, offset_y).
    Zwraca (None, 0, 0), jeśli okno nie zostało znalezione.
    Ta metoda, "Wizja Selektywna", drastycznie redukuje rozmiar danych wysyłanych do API.
    """
    try:
        windows = gw.getWindowsWithTitle(window_title_keyword)
        if not windows:
            return None, 0, 0

        # Wybieramy pierwsze trafienie
        target_win = windows[0]

        # Jeśli okno jest zminimalizowane, nie da się go poprawnie skopiować przez standardowe współrzędne
        if target_win.isMinimized:
            target_win.restore()

        # Zabezpieczenie przed niewłaściwymi wymiarami (np. błędy API Windows)
        if target_win.width <= 0 or target_win.height <= 0:
            return None, 0, 0

        with mss.mss() as sct:
            # Definiujemy wycinek bazujący na koordynatach okna
            monitor_roi = {
                "top": target_win.top,
                "left": target_win.left,
                "width": target_win.width,
                "height": target_win.height
            }
            screenshot_bgra = sct.grab(monitor_roi)
            img = Image.frombytes("RGB", screenshot_bgra.size, screenshot_bgra.bgra, "raw", "BGRX")

            # Zwracamy obraz oraz pozycje lewego górnego rogu (offsety), aby skorygować w systemie koordynaty lokalne na globalne
            return img, target_win.left, target_win.top
    except Exception as e:
        print(f"Błąd przechwytywania ROI: {e}")
        return None, 0, 0

def capture_region(center_x: int, center_y: int, size: int = 100) -> Image.Image:
    """
    Przechwytuje mały wycinek ekranu o rozmiarze size x size, którego środek to (center_x, center_y).
    Używane do optymalizacji szybkości testów OCR, odciążając obróbkę całego ekranu.
    """
    half_size = size // 2

    # Zapobieganie wyjściu poza krawędzie ekranu ujemnymi wymiarami
    top = max(0, center_y - half_size)
    left = max(0, center_x - half_size)

    with mss.mss() as sct:
        monitor_roi = {
            "top": top,
            "left": left,
            "width": size,
            "height": size
        }
        try:
            screenshot_bgra = sct.grab(monitor_roi)
            img = Image.frombytes("RGB", screenshot_bgra.size, screenshot_bgra.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            print(f"Błąd przy przechwytywaniu mikro-regionu: {e}")
            return None
