from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://vsm:vsm@localhost:5432/vsm"
    # Shared password of the fictional demo accounts created by `python -m app.seed`.
    demo_password: str = "vsm-demo"
    session_ttl_hours: int = 12
    # Set to true when the app is served over HTTPS so the session cookie is never sent in clear text.
    cookie_secure: bool = False
    # Comma-separated origins allowed to call the API from another origin; empty = same origin only.
    cors_origins: str = ""
    # Key for /integrations/* (HR, LMS). Empty disables the integration API.
    integration_api_key: str = ""
    # Sign-in throttling: after this many wrong passwords in a row the login is locked for a while.
    login_max_failures: int = 5
    login_lock_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
