class UserAlreadyRegistered(Exception):
    def __init__(self, message="User already registered"):
        super().__init__(message)
