from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Text, Enum as SQLEnum
from shared.db.base import Base
from datetime import datetime
import enum
from typing import Optional
from shared.db.project_models import Project
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.db.project_models import Project

class UserStatus(str, enum.Enum):
    NEW = "new" # новичок, не зарегался
    WAIT = "wait" # ожидает проверки
    FAIL = "fail" # не прошел проверку
    READY = "ready" # проверен, может кидать преокты


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # Telegram ID
    username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True) # Telegram UserName

    name: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    portfolio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    about: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.NEW,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    projects: Mapped[list["Project"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )