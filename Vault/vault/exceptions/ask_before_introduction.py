from typing import Any

from vault.exceptions.command_exception import CommandException


class AskBeforeIntroduction(CommandException):
    def __init__(self, data=None):
        super().__init__()
        if data is None:
            data = {}
        self.data = data
