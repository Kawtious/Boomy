class GameNotStarted(Exception):
    def __init__(self, message="Game not started"):
        super().__init__(message)
