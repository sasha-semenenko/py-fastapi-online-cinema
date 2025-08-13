import os
from pathlib import Path

from pydantic_settings import BaseSettings


from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    BASE_DIR: Path = Path.cwd()
    POSTGRES_URL: str = os.getenv("POSTGRESQL_URL")
    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS")
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH")
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM")
    LOGIN_TIME_DAYS: int = 7

    model_config = {
        "from_attributes": True
    }

settings = Settings()
