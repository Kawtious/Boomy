from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from vault.data.database.cartridge import Cartridge


class NESCartridge(Cartridge):
    __tablename__ = 'nes_cartridge'

    __mapper_args__ = {
        "polymorphic_identity": "nes_cartridge",
    }

    id: Mapped[int] = mapped_column(ForeignKey("cartridge.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="nes_cartridges")
