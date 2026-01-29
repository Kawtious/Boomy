class FrameLimitReached(Exception):
    def __init__(self, message="Frame limit reached"):
        super().__init__(message)
