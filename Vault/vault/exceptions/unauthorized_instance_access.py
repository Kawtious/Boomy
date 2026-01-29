class UnauthorizedInstanceAccess(Exception):
    def __init__(self, message="Unauthorized instance access"):
        super().__init__(message)
