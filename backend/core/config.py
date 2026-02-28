from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
import pathlib

current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parent.parent
env_file_path = project_root / ".env"

class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://"
            f"{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

config = Settings()