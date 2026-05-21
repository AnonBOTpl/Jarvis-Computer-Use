import pytesseract
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)

# Konfiguracja ścieżki dla systemu Windows (może być nadpisana przez config.json)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def set_tesseract_path(path: str):
    """Ustawia niestandardową ścieżkę do Tesseract-OCR."""
    global TESSERACT_PATH
    if os.path.exists(path):
        TESSERACT_PATH = path
        pytesseract.pytesseract.tesseract_cmd = path
        logger.info(f"Ustawiono ścieżkę Tesseract: {path}")
    else:
        logger.warning(f"Podana ścieżka Tesseract nie istnieje: {path}")

def extract_text_from_image(image: Image.Image, lang: str = "pol") -> str:
    """
    Przyjmuje obraz PIL i wykonuje na nim lokalny OCR za pomocą Tesseract.
    Zwraca wyciągnięty tekst. Timeout włączony na poziomie funkcji ułatwia powrót do głównej pętli
    w przypadku zablokowania lub braku odpowiedzi przez tesseract w określonym czasie (2s).
    Parametr `lang` pozwala wybrać język (domyślnie 'pol', może być 'pol+eng' itp.).
    """
    try:
        gray_image = image.convert('L')
        text = pytesseract.image_to_string(gray_image, lang=lang, timeout=2.0)
        return text.strip()
    except Exception as e:
        logger.error(f"Błąd silnika OCR lub przekroczony czas weryfikacji: {e}")
        return ""

def is_text_visible(image: Image.Image, search_text: str, lang: str = "pol") -> bool:
    """Sprawdza czy wskazany ciąg znaków jest widoczny na danym wycinku ekranu."""
    extracted_text = extract_text_from_image(image, lang=lang).lower()
    return search_text.lower() in extracted_text
