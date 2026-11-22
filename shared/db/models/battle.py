from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.db.models.base import Base
from shared.db.models.project import Project, Category, SubCategory
from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Integer, Text, UniqueConstraint
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.db.models.project import Project


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id"), nullable=False
    )

    sub_category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sub_categories.id"), nullable=True
    )

    category: Mapped["Category"] = relationship(foreign_keys=[category_id])
    sub_category: Mapped["SubCategory"] = relationship(foreign_keys=[sub_category_id])

    __table_args__ = (
        UniqueConstraint("number", name="uq_battles_number"),
    )

    project_links: Mapped[list["BattleProject"]] = relationship(
        back_populates="battle",
        cascade="all, delete-orphan",
    )


class BattleProject(Base):
    __tablename__ = "battle_projects"

    battle_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("battles.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), primary_key=True
    )

    battle: Mapped["Battle"] = relationship(back_populates="project_links")
    project: Mapped["Project"] = relationship(back_populates="battle_links")

