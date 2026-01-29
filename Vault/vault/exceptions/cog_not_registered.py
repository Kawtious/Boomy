class CogNotRegistered(Exception):
    def __init__(self, message="Cog not registered"):
        super().__init__(message)
