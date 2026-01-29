class UnauthorizedLayoutAccess(Exception):
    def __init__(self, message="Unauthorized layout access"):
        super().__init__(message)
