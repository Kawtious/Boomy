import abc
from typing import Type

from PIL import Image
from vault.data.database.cartridge import Cartridge
from vault.data.database.user import User

from emulator.game.base_game_instance import BaseGameInstance


class BaseEmulator(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        self.game_instance_manager = None

    @abc.abstractmethod
    def start(self, cartridge: Cartridge, user: User | Type[User]) -> tuple[BaseGameInstance, Image]:
        pass

    @abc.abstractmethod
    def input(self, cartridge: Cartridge, user: User | Type[User], button=None) -> tuple[BaseGameInstance, list[Image]]:
        pass
