import pytesseract
from PIL import Image
import os

# Konfiguracja ścieżki dla systemu Windows
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extract_text_from_image(image: Image.Image) -> str:
    """
    Przyjmuje obraz PIL i wykonuje na nim lokalny OCR za pomocą Tesseract.
    Zwraca wyciągnięty tekst. Ze względu na wydajność, operacja powinna
    być wykonywana w osobnym wątku.
    """
    try:
        # Konwersja obrazu do skali szarości poprawia jakość OCR
        gray_image = image.convert('L')
        # Dodanie języka polskiego dla tesseract (wymaga zainstalowanych paczek językowych w OS)
        # Będziemy używać parametru pol+eng lub zaufamy domyślnemu j. polskiemu systemu.
        text = pytesseract.image_to_string(gray_image, lang='pol+eng')
        return text.strip()
    except Exception as e:
        print(f"Błąd silnika OCR: {e}")
        return ""

def is_text_visible(image: Image.Image, search_text: str) -> bool:
    """Sprawdza czy wskazany ciąg znaków jest widoczny na danym wycinku ekranu."""
    extracted_text = extract_text_from_image(image).lower()
    return search_text.lower() in extracted_text
