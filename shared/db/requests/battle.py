from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import update

from shared.db.models.project import Project, ProjectStatus
from shared.db.models.battle import Battle, BattleProject
from shared.db.models.user import User
from shared.db.models.project import Project

import datetime
from collections.abc import Sequence


async def create_battle(
    session: AsyncSession,
    number: int,
    link: str,
    category_id: int,
    project_ids: Sequence[int],
    theme: str | None = None,
    sub_category_id: int | None = None,
    date: datetime.date | None = None,
) -> Battle:
    battle_date = date if date is not None else datetime.date.today()
    unique_project_ids = list(dict.fromkeys(project_ids))

    battle = Battle(
        number=number,
        date=battle_date,
        link=link,
        theme=theme,
        category_id=category_id,
        sub_category_id=sub_category_id,
        project_links=[
            BattleProject(project_id=project_id)
            for project_id in unique_project_ids
        ],
    )

    session.add(battle)

    if unique_project_ids:
        await session.execute(
            update(Project)
            .where(Project.id.in_(unique_project_ids))
            .values(status=ProjectStatus.ON_BATTLE)
        )

    await session.flush()
    await session.commit()
    await session.refresh(battle)
    return battle


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


async def count_battle_projects_by_category(
    session: AsyncSession,
    category_id: int,
) -> int:
    """Возвращает общее количество записей в battle_projects для батлов с заданным category_id."""
    stmt = (
        select(func.count())
        .select_from(BattleProject)
        .join(Battle, Battle.id == BattleProject.battle_id)
        .where(Battle.category_id == category_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


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