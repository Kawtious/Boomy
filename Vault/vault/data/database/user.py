from typing import List

from sqlalchemy import Column, BigInteger, Boolean
from sqlalchemy.orm import Mapped, relationship

from vault.data.database.base import Base
from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.gameboy_profile import GameBoyProfile
from vault.data.database.nes_cartridge import NESCartridge
from vault.data.database.pokemon import Pokemon
from vault.data.database.statistics import Statistics


class User(Base):
    __tablename__ = 'user'

    id = Column(BigInteger, primary_key=True)
    premium = Column(Boolean, default=False, nullable=False)
    statistics: Mapped[Statistics] = relationship(back_populates="user", cascade="all, delete-orphan")
    pokemon: Mapped[Pokemon] = relationship(back_populates="user", cascade="all, delete-orphan")

    gameboy_cartridges: Mapped[List[GameBoyCartridge]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    nes_cartridges: Mapped[List[NESCartridge]] = relationship(back_populates="user", cascade="all, delete-orphan")

    gameboy_profile: Mapped[GameBoyProfile] = relationship(back_populates="user", cascade="all, delete-orphan")
