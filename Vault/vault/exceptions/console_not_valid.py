class ConsoleNotValid(Exception):
    def __init__(self, message="Console not valid"):
        super().__init__(message)
