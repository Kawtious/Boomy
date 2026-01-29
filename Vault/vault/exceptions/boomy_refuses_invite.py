class BoomyRefusesInvite(Exception):
    def __init__(self, message="Boomy refuses invite"):
        super().__init__(message)
