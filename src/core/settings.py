from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Crustdata AI Assistant"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- Google Gemini ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    # --- Upstash Redis ---
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # --- Qdrant Vector DB ---
    QDRANT_ENDPOINT: str = "http://localhost:6333"
    QDRANT_KEY: str = ""

    # --- PostgreSQL Database ---
    POSTGRES_USERNAME: str = ""
    POSTGRES_DB_PASSWORD: str = ""
    POSTGRES_DB_HOST: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
