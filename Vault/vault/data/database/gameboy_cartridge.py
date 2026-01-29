from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vault.data.database.cartridge import Cartridge


class GameBoyCartridge(Cartridge):
    __tablename__ = 'gameboy_cartridge'

    __mapper_args__ = {
        "polymorphic_identity": "gameboy_cartridge",
    }

    id: Mapped[int] = mapped_column(ForeignKey("cartridge.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="gameboy_cartridges")

    border = Column(String(256), default="border.png", nullable=True)
    boot_animation = Column(String(256), default="boot.gif", nullable=True)
