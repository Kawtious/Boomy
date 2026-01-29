class InvalidGameTitle(Exception):
    def __init__(self, message="Invalid game title"):
        super().__init__(message)
