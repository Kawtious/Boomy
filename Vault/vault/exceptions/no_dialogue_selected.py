class NoDialogueSelected(Exception):
    def __init__(self, message="No dialogue selected"):
        super().__init__(message)
