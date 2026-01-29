import hashlib

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.util.preloaded import orm

from vault.data.database.base import Base


class Cartridge(Base):
    __tablename__ = 'cartridge'

    __mapper_args__ = {
        "polymorphic_identity": "cartridge",
        "polymorphic_on": "type",
    }

    __table_args__ = (
        UniqueConstraint('user_id', 'type', 'title', name='uq_user_type_title'),
        UniqueConstraint('user_id', 'rom_hash', name='uq_user_rom_hash'),
    )

    id = Column(Integer, primary_key=True)
    type = Column(String(32), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    title = Column(String(32), nullable=False)
    icon = Column(String(256), nullable=True)

    play_time = Column(Integer, default=0, nullable=False)

    rom = Column(LONGBLOB, nullable=False)
    rom_hash = Column(String(64), nullable=False)

    state = Column(LONGBLOB, nullable=True)
    save_state = Column(LONGBLOB, nullable=True)

    @staticmethod
    def generate_rom_hash(rom_bytes: bytes) -> str:
        return hashlib.sha256(rom_bytes).hexdigest()

    @orm.reconstructor
    def init_on_load(self):
        # Called when object is loaded from DB
        pass

    @orm.validates('rom')
    def __validate_rom(self, key, value):
        # Automatically update rom_hash on setting rom
        self.rom_hash = self.generate_rom_hash(value)
        return value
