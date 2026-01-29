class GameInstanceNotFound(Exception):
    def __init__(self, message="Game instance not found"):
        super().__init__(message)
