from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Le indicamos a Pydantic que lea el archivo .env en la raíz
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instanciamos la clase para importar "settings" directamente en otros archivos
settings = Settings()