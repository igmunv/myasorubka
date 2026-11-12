from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from config import config

DATABASE_URL = f"postgresql+asyncpg://{config.postgres_user.get_secret_value()}:{config.postgres_password.get_secret_value()}@{config.postgres_host.get_secret_value()}:{config.postgres_port}/{config.postgres_db.get_secret_value()}"

engine = create_async_engine(
    DATABASE_URL, 
    echo=False
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase, AsyncAttrs):
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)