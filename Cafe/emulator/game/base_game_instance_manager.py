import abc
import asyncio
import time
from typing import Optional

from vault.data.database.cartridge import Cartridge
from vault.data.database.user import User
from vault.exceptions.cartridge_not_found import GameNotStarted
from vault.exceptions.not_enough_joypads import NotEnoughJoypads
from vault.exceptions.user_already_invited import UserAlreadyInvited
from vault.exceptions.user_is_cartridge_owner import UserIsCartridgeOwner
from vault.exceptions.user_not_invited import UserNotInvited

from emulator.game.base_game_instance import BaseGameInstance


class BaseGameInstanceManager(abc.ABC):
    CLEANUP_INTERVAL = 60  # seconds
    INSTANCE_TIMEOUT = 1 * 60  # 10 minutes

    @abc.abstractmethod
    def __init__(self):
        self.instances: dict[Cartridge, tuple[BaseGameInstance, list[int]]] = {}
        self.last_used: dict[Cartridge, float] = {}

        self.cleanup_task: Optional[asyncio.Task] = None
        self.should_stop: bool = False

        self.start_cleanup_loop()

    def start_cleanup_loop(self):
        if not self.cleanup_task or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self.cleanup_inactive_instances())

    async def cleanup_inactive_instances(self):
        while not self.should_stop:
            await asyncio.sleep(self.CLEANUP_INTERVAL)
            now = time.time()
            to_remove: list[Cartridge] = []

            for key, last_used in self.last_used.items():
                if now - last_used > self.INSTANCE_TIMEOUT:
                    to_remove.append(key)

            for key in to_remove:
                self.last_used.pop(key, None)

                instance = self.instances.pop(key, None)
                if instance:
                    instance[0].stop()

    @abc.abstractmethod
    def get_game_instance(self, cartridge: Cartridge, user: User) -> tuple[BaseGameInstance, int]:
        pass

    def get_instance_from_user(self, user: User):
        for cartridge in self.instances:
            if user.id == cartridge.user_id:
                instance, users = self.instances[cartridge]
                return cartridge, instance, users

        raise GameNotStarted()

    def add_user(self, cartridge: Cartridge, user: User):
        if user.id == cartridge.user_id:
            raise UserIsCartridgeOwner()

        if cartridge not in self.instances:
            raise GameNotStarted()

        instance, users = self.instances[cartridge]

        if len(users) >= instance.max_players:
            raise NotEnoughJoypads()

        if user.id in users:
            raise UserAlreadyInvited()

        users.append(user.id)

    def remove_user(self, cartridge: Cartridge, user: User):
        if user.id == cartridge.user_id:
            raise UserIsCartridgeOwner()

        if cartridge not in self.instances:
            raise GameNotStarted()

        instance, users = self.instances[cartridge]

        if user.id not in users:
            raise UserNotInvited()

        users.pop(users.index(user.id))

    def shutdown(self):
        self.should_stop = True

        for instance in self.instances.values():
            instance[0].stop()
