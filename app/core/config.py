from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    HF_ACCESS_TOKEN: str
    FRONTEND_URL: str
    SECRET: str
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def enviroment_variables():
    return Settings()