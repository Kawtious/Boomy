class LanguageNotAvailable(Exception):
    def __init__(self, message="Language not available"):
        super().__init__(message)
