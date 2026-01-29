class CafeRefusesInvite(Exception):
    def __init__(self, message="Café refuses invite"):
        super().__init__(message)
