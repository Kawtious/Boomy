class InterruptedTalk(Exception):
    def __init__(self, message="Interrupted talk", user_id: int = None):
        super().__init__(message)
        self.user_id = user_id
