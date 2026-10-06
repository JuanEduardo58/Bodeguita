from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Fuera de Docker se lee el .env de la raíz del repo; en Docker, las variables de compose.
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 720  # una jornada del colmado


settings = Settings()
