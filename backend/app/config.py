"""アプリケーション設定。環境変数（または backend/.env）で上書きできる。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./chat.db"
    # カンマ区切りで複数指定可能（例: "http://localhost:3000,http://127.0.0.1:3000"）
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    default_room_name: str = "General"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
