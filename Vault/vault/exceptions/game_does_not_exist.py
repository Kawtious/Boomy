class GameDoesNotExist(Exception):
    def __init__(self, message="Game does not exist"):
        super().__init__(message)
