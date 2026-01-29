from enum import Enum

from sqlalchemy import Integer, Column, ForeignKey, Boolean, TypeDecorator, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vault.data.database.base import Base


class Collectibles(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class CollectiblesEnumListType(TypeDecorator):
    impl = JSON  # Native MySQL JSON column

    def process_bind_param(self, value, dialect):
        if value is not None:
            # Convert list of Enums to list of strings
            return [v.value for v in value]
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            # Convert list of strings back to list of Enum values
            return [Collectibles(v) for v in value]
        return None


class Statistics(Base):
    __tablename__ = 'statistics'

    id = Column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="statistics")

    collectibles = Column(CollectiblesEnumListType, default=lambda: {}, nullable=False)

    met_boomy = Column(Boolean, default=False, nullable=False)

    knows_boomy = Column(Boolean, default=False, nullable=False)
    knows_cafe = Column(Boolean, default=False, nullable=False)
    knows_berry = Column(Boolean, default=False, nullable=False)
    knows_jax = Column(Boolean, default=False, nullable=False)
    knows_dad = Column(Boolean, default=False, nullable=False)
    knows_mystery_console = Column(Boolean, default=False, nullable=False)
    knows_boomy_ears = Column(Boolean, default=False, nullable=False)
