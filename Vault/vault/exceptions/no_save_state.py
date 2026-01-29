class NoSaveState(Exception):
    def __init__(self, message="No save state", user_id: int = None):
        super().__init__(message)
        self.user_id = user_id
