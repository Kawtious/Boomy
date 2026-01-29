from sqlalchemy import Column, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vault.data.database.base import Base


class Pokemon(Base):
    __tablename__ = 'pokemon'

    id = Column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="pokemon")

    mon = Column(Text, nullable=True)  # raw Showdown team string
