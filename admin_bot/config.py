from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional

class Settings(BaseSettings):

    admin_bot_token: SecretStr

    superuser_tg_id: int

    postgres_user: SecretStr
    postgres_password: SecretStr
    postgres_host: SecretStr
    postgres_port: int
    postgres_db: SecretStr

    redis_password: SecretStr

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

    proxy_url: Optional[SecretStr] = None

config = Settings()