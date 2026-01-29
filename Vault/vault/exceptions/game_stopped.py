class GameStopped(Exception):
    def __init__(self, message="Game is stopped"):
        super().__init__(message)
