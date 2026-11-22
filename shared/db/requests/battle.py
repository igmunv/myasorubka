from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.db.models.battle import Battle, BattleProject


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