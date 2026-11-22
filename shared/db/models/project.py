from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func, Text, Enum as SQLEnum
from shared.db.models.base import Base
from datetime import datetime
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.db.models.user import User


class ProjectStatus(str, enum.Enum):
    WAIT = "wait" # ожидает проверки
    READY = "ready" # проверен, ожидает батл
    FAIL = "fail" # не прошел проверку
    ON_BATTLE = "on_battle" # сейчас на батле
    POST_BATTLE = "post_battle" # уже был на батле


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    desc: Mapped[str] = mapped_column(String(256), nullable=False)

    sub_categories: Mapped[list["SubCategory"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )
    
    projects: Mapped[list["Project"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class SubCategory(Base):
    __tablename__ = "sub_categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    desc: Mapped[str] = mapped_column(String(256), nullable=False)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped["Category"] = relationship(back_populates="sub_categories")

    projects: Mapped[list["Project"]] = relationship(
        back_populates="sub_category", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(64), nullable=False)
    summ: Mapped[str] = mapped_column(String(128), nullable=False)
    uniq: Mapped[str] = mapped_column(String(128), nullable=False)

    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus), 
        default=ProjectStatus.WAIT, 
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # ForeignKeys
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    sub_category_id: Mapped[int] = mapped_column(
        ForeignKey("sub_categories.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="projects")
    category: Mapped["Category"] = relationship(back_populates="projects")
    sub_category: Mapped["SubCategory"] = relationship(back_populates="projects")
