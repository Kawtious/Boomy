class UserAlreadyInvited(Exception):
    def __init__(self, message="User already invited"):
        super().__init__(message)
