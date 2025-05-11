from pyarabic.araby import strip_tashkeel, normalize_hamza

def preprocess_arabic_text(text):
    text = strip_tashkeel(text)  # Remove diacritics
    text = normalize_hamza(text)  # Normalize hamza characters
    return text