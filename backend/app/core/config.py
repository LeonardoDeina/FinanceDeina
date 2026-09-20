from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://financedeina:financedeina@localhost:3306/financedeina"
    default_base_currency: str = "EUR"
    default_timezone: str = "Europe/Lisbon"
    backup_dir: str = "/data/backups"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
