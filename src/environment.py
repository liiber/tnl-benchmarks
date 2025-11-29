from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Environment(BaseSettings):
    APP_PORT: int = 8000

    DB_USER: str = Field(..., min_length=3)
    DB_PASSWORD: str = Field(..., min_length=3)
    DB_NAME: str = Field(..., min_length=3)
    DB_HOST: str = Field(..., min_length=3)
    DB_PORT: int = 5432

    model_config = SettingsConfigDict(env_file=".env")

ENV = Environment()
