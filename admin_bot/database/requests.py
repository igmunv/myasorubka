from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from database.models import RegistrationModeration
from sqlalchemy import func

async def create_moderation_record(session: AsyncSession, user_id: int, reason: str):
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