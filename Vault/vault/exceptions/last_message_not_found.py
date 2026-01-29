class LastMessageNotFound(Exception):
    def __init__(self, message="Last message not found"):
        super().__init__(message)
