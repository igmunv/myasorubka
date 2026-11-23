from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.db.models.battle import Battle, BattleProject
from shared.db.models.user import User
from shared.db.models.project import Project


async def get_latest_battle(session: AsyncSession) -> Battle | None:
    """ Возвращает последний батл """
    stmt = (
        select(Battle)
        .options(
            selectinload(Battle.project_links).selectinload(BattleProject.project),
        )
        .order_by(Battle.date.desc(), Battle.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def count_battle_projects_by_sub_category(
    session: AsyncSession,
    sub_category_id: int,
) -> int:
    """Возвращает общее количество записей в battle_projects для батлов с заданным sub_category_id."""
    stmt = (
        select(func.count())
        .select_from(BattleProject)
        .join(Battle, Battle.id == BattleProject.battle_id)
        .where(Battle.sub_category_id == sub_category_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def count_user_battle_participations(
    session: AsyncSession,
    user: User,
) -> int:
    """Возвращает количество участий проектов пользователя в батлах."""
    stmt = (
        select(func.count(BattleProject.battle_id))
        .select_from(BattleProject)
        .join(Project, Project.id == BattleProject.project_id)
        .where(Project.user_id == user.id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_battle_users(
    session: AsyncSession,
    battle: Battle,
) -> list[User]:
    """Возвращает уникальных пользователей (авторов проектов), участвовавших в батле."""
    stmt = (
        select(User)
        .join(Project, Project.user_id == User.id)
        .join(BattleProject, BattleProject.project_id == Project.id)
        .where(BattleProject.battle_id == battle.id)
        .distinct()
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())