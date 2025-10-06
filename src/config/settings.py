import os
from pathlib import Path

from pydantic_settings import BaseSettings

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_EMAIL_TEMPLATES_DIR: str = str(BASE_DIR / "notifications" / "templates")
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = os.getenv("ACTIVATION_EMAIL_TEMPLATE_NAME")
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = os.getenv("ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME")
    PASSWORD_RESET_TEMPLATE_NAME: str = os.getenv("PASSWORD_RESET_TEMPLATE_NAME")
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = os.getenv("PASSWORD_RESET_COMPLETE_TEMPLATE_NAME")

    POSTGRES_URL: str = os.getenv("POSTGRESQL_URL")
    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS")
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH")
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM")
    LOGIN_TIME_DAYS: int = 7

    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "host")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", 25))
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER", "testuser")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD", "test_password")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"


    model_config = {
        "from_attributes": True
    }

settings = Settings()
