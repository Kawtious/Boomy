class LanguageDirectoryNotFound(Exception):
    def __init__(self, lang_path):
        super().__init__(f"Language directory '{lang_path}' not found.")
