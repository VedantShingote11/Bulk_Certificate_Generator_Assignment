from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "changeme"
    ENVIRONMENT: str = "development"
    CERTIFICATE_OUTPUT_DIR: str = "app/static/certificates"
    BASE_URL: str = "http://localhost:8000"

    model_config = {"env_file": ".env"}


settings = Settings()
