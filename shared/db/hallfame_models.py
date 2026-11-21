from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Text, Boolean, Enum as SQLEnum
from datetime import datetime
from typing import Optional
from database.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.models import Project


class HallOfFame(Base):
    __tablename__ = "hall_of_fame"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped["Project"] = relationship()