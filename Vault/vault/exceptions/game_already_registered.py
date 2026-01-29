class GameAlreadyRegistered(Exception):
    def __init__(self, message="Game already registered"):
        super().__init__(message)
