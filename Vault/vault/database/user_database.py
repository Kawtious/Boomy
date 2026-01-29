from typing import Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from vault.data.database.gameboy_profile import GameBoyProfile
from vault.data.database.pokemon import Pokemon
from vault.data.database.statistics import Statistics
from vault.data.database.user import User
from vault.exceptions.user_already_registered import UserAlreadyRegistered
from vault.exceptions.user_not_registered import UserNotRegistered


class UserDatabase:
    def __init__(self, session: Session):
        self.__session = session

    def register(self, user: User):
        if self.__session.query(User).filter_by(id=user.id).first():
            raise UserAlreadyRegistered()

        try:
            self.__session.add(user)
            self.__session.commit()
        except IntegrityError:
            self.__session.rollback()
            raise IntegrityError

    def update(self, user_id: int, updated_user: User):
        user = self.__session.query(User).filter_by(id=user_id).first()

        if user is None:
            raise UserNotRegistered()

        user = updated_user

        try:
            self.__session.commit()
        except IntegrityError:
            self.__session.rollback()
            raise IntegrityError

    def fetch(self, user_id: int) -> User | Type[User]:
        user = self.__session.query(User).filter_by(id=user_id).options(
            joinedload(User.statistics),
            joinedload(User.pokemon),
            joinedload(User.gameboy_profile),
            joinedload(User.gameboy_cartridges),
            joinedload(User.nes_cartridges)
        ).first()

        if user is None:
            raise UserNotRegistered()

        return user

    def fetch_or_register(self, user_id: int) -> User | Type[User]:
        try:
            return self.fetch(user_id)
        except UserNotRegistered:
            user = User(
                id=user_id,
                statistics=Statistics(),
                pokemon=Pokemon(),
                gameboy_profile=GameBoyProfile()
            )

            self.register(user)

            return user

    def delete(self, user_id: int):
        user = self.__session.query(User).filter_by(id=user_id).first()

        if user is None:
            raise UserNotRegistered()

        try:
            self.__session.delete(user)
            self.__session.commit()
        except IntegrityError:
            self.__session.rollback()
            raise IntegrityError
