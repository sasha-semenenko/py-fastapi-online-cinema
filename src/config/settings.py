import os
from pathlib import Path

from pydantic_settings import BaseSettings


from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    BASE_DIR: Path = Path.cwd()
    POSTGRES_URL: str = os.getenv("POSTGRESQL_URL")

    model_config = {
        "from_attributes": True
    }

settings = Settings()
