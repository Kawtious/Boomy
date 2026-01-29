class UnauthorizedJoypadAccess(Exception):
    def __init__(self, message="Unauthorized joypad access"):
        super().__init__(message)
