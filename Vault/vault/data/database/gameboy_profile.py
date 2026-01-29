from sqlalchemy import Column, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vault.data.database.base import Base


class GameBoyProfile(Base):
    __tablename__ = 'gameboy_profile'

    id = Column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="gameboy_profile")

    custom_border = Column(String(256), nullable=True)

    enable_color = Column(Boolean, default=True, nullable=False)
    enable_border = Column(Boolean, default=True, nullable=False)
