class GuildOnlyCommand(Exception):
    def __init__(self, message="Guild only command"):
        super().__init__(message)
