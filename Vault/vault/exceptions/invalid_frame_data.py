class InvalidFrameData(Exception):
    def __init__(self, message="Invalid frame data"):
        super().__init__(message)
