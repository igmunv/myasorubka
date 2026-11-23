from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
import shared.db.models.battle

from shared.config import config

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{config.postgres_user.get_secret_value()}:"
    f"{config.postgres_password.get_secret_value()}@"
    f"{config.postgres_host.get_secret_value()}:"
    f"{config.postgres_port}/"
    f"{config.postgres_db.get_secret_value()}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def init_db(base: type[DeclarativeBase]) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)