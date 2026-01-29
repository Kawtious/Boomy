class NoAttachments(Exception):
    def __init__(self, message="No attachments"):
        super().__init__(message)
