import re

def clean_text(text: str) -> str:
    # Убираем лишние пробелы и спецсимволы
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text.lower()

def normalize_term(text: str) -> str:
    # Убираем всё кроме букв и пробелов
    text = re.sub(r'[^\w\s]', '', text)
    return clean_text(text)