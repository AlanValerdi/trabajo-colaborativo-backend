from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SQLALCHEMY_DATABASE_URL: str = (
        "mysql+pymysql://admin:123@db:3306/tc-db"
    )


settings = Settings()
