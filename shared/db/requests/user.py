from typing import Optional

from sqlalchemy import desc, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from shared.db.models.user import User, UserStatus


async def get_next_waiting_user(session: AsyncSession) -> Optional[User]:
    stmt = (
        select(User)
        .where(User.status == UserStatus.WAIT)
        .order_by(User.created_at.asc(), User.id.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()