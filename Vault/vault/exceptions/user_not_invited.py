class UserNotInvited(Exception):
    def __init__(self, message="User not invited"):
        super().__init__(message)
