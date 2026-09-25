from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://vsm:vsm@localhost:5432/vsm"

    class Config:
        env_file = ".env"


settings = Settings()
