from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Text, Boolean, Enum as SQLEnum
from database.base import Base
from typing import List
from datetime import datetime
import enum
from typing import Optional


class RegistrationModeration(Base):
    __tablename__ = "registration_moderation"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # Telegram ID
    reason: Mapped[str] = mapped_column(String(300), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
