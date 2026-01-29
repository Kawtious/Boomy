class BerryRefusesInvite(Exception):
    def __init__(self, message="Berry refuses invite"):
        super().__init__(message)
