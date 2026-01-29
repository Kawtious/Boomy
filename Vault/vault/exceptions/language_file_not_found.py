class LanguageFileNotFound(Exception):
    def __init__(self, lang):
        super().__init__(f"Language file '{lang}.json' not found.")
