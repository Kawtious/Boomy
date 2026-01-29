from typing import Any


class CommandException(Exception):
    def __init__(self, data: dict[str, Any]):
        super().__init__()
        self.data = data
