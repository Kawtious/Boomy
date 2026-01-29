import abc

from PIL import Image
from vault.exceptions.no_previous_state import NoPreviousState


class BaseGameInstance(abc.ABC):
    __STATE_HISTORY_LIMIT: int = 10

    @abc.abstractmethod
    def __init__(self):
        self.state_history: list[bytes] = []

    @property
    @abc.abstractmethod
    def max_players(self) -> int:
        return 0

    @abc.abstractmethod
    def restart(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @property
    @abc.abstractmethod
    def save_state(self) -> bytes:
        pass

    @abc.abstractmethod
    def load_state(self, save_state):
        pass

    def previous_state(self):
        if not self.state_history:
            raise NoPreviousState()

        save_state = self.state_history.pop()
        self.load_state(save_state)

    def save_state_to_history(self, save_state: bytes):
        self.state_history.append(save_state)

        if len(self.state_history) > self.__STATE_HISTORY_LIMIT:
            del self.state_history[0]

    @abc.abstractmethod
    def screenshot(self) -> Image:
        pass

    @abc.abstractmethod
    def input(self, button, duration_frames=10):
        pass
