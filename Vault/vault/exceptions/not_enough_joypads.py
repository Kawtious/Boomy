class NotEnoughJoypads(Exception):
    def __init__(self, message="Not enough joypads"):
        super().__init__(message)
