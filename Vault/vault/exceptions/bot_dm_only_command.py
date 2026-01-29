class BotDMOnlyCommand(Exception):
    def __init__(self, message="Bot DM only command"):
        super().__init__(message)
