from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

import importlib
import pkgutil

import shared.db.models as models_pkg

for _, module_name, _ in pkgutil.iter_modules(models_pkg.__path__):
    importlib.import_module(f"{models_pkg.__name__}.{module_name}")

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
