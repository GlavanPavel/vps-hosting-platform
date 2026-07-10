from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
import pathlib

current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parent.parent
env_file_path = project_root / ".env"

class Settings(BaseSettings):
    # mariadb
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # openstack
    OS_AUTH_URL: str
    OS_PROJECT_NAME: str
    OS_USERNAME: str
    OS_PASSWORD: str
    OS_USER_DOMAIN_NAME: str = "Default"
    OS_PROJECT_DOMAIN_NAME: str = "Default"

    # openstack networking
    OS_EXTERNAL_NETWORK: str = "public"

    # jwt auth
    JWT_SECRET_KEY: str = "devsecretsecretkey"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # influxdb
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_ADMIN_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str

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