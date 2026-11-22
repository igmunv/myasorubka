from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models.moderation import ProjectsModeration, RegistrationModeration


async def create_reg_moderation_record(session: AsyncSession, user_id: int, reason: str):
    # Составляем инструкцию вставки
    stmt = insert(RegistrationModeration).values(
        user_id=user_id,
        reason=reason
    )
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id'],
        set_={
            'reason': stmt.excluded.reason,
            'created_at': func.now()  
        }
    )
    
    await session.execute(stmt)
    await session.commit()


async def create_proj_moderation_record(session: AsyncSession, project_id: int, reason: str):
    # Составляем инструкцию вставки
    stmt = insert(ProjectsModeration).values(
        project_id=project_id,
        reason=reason
    )
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['project_id'],
        set_={
            'reason': stmt.excluded.reason,
            'created_at': func.now()  
        }
    )
    
    await session.execute(stmt)
    await session.commit()