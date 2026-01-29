from typing import Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from vault.data.database.cartridge import Cartridge
from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.nes_cartridge import NESCartridge
from vault.data.database.user import User
from vault.exceptions.game_already_registered import GameAlreadyRegistered
from vault.exceptions.game_does_not_exist import GameDoesNotExist


class CartridgeDatabase:
    def __init__(self, session: Session):
        self.__session = session

    def register(self, cartridge: Cartridge):
        if self.__session.query(Cartridge).filter_by(title=cartridge.title).first():
            raise GameAlreadyRegistered()

        try:
            self.__session.add(cartridge)
            self.__session.commit()
        except IntegrityError:
            self.__session.rollback()
            raise GameAlreadyRegistered()

    def fetch_gameboy_cartridge(self, user: User, title: str) -> GameBoyCartridge | Type[GameBoyCartridge]:
        cartridge = self.__session.query(GameBoyCartridge).filter_by(user=user, title=title).first()

        if cartridge is None:
            raise GameDoesNotExist()

        return cartridge

    def fetch_nes_cartridge(self, user: User, title: str) -> NESCartridge | Type[NESCartridge]:
        cartridge = self.__session.query(NESCartridge).filter_by(user=user, title=title).first()

        if cartridge is None:
            raise GameDoesNotExist()

        return cartridge
