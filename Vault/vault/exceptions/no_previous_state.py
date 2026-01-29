class NoPreviousState(Exception):
    def __init__(self, message="No previous state"):
        super().__init__(message)
