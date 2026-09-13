from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SQLALCHEMY_DATABASE_URL: str = (
        "mysql+pymysql://admin:123@db:3306/tc-db"
    )

    # JWT
    SECRET_KEY: str = "changeme-super-secret-key-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
