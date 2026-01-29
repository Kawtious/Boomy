class UserIsCartridgeOwner(Exception):
    def __init__(self, message="User is cartridge owner"):
        super().__init__(message)
