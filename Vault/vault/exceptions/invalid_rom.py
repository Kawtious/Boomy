class InvalidROM(Exception):
    def __init__(self, message="Invalid ROM"):
        super().__init__(message)
