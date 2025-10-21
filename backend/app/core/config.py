from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "default-secret-key"
    environment: str = "development"
    anthropic_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
