from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str
    STORAGE_ROOT: str = "/storage"

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MIN: int = 720

    ADMIN_LOGIN: str = "admin000"
    ADMIN_PASSWORD: str = "admin"
    ADMIN_FIRST_NAME: str = "Mariia"
    ADMIN_LAST_NAME: str = "Haidei"
    ADMIN_ORG: str = "MSU"
    ADMIN_EMAIL: str = "st02220069@gse.cs.msu.ru"

settings = Settings()