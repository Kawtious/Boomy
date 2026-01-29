class UserNotRegistered(Exception):
    def __init__(self, message="User not registered"):
        super().__init__(message)
