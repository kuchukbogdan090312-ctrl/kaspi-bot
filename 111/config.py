from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    KASPI_PHONE: str = "+77001234567"
    KASPI_QR_URL: str = ""
    COMMUNITY_LINK: str = ""
    DB_PATH: str = "database/bot.db"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
