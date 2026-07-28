from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    current_homework: str = ""

    # Staging
    staging_repo: str = ""
    staging_cove_url: str = ""
    staging_cove_api_key: str = ""
    staging_cove_project: str = ""

    # Production
    production_repo: str = ""
    production_cove_url: str = ""
    production_cove_api_key: str = ""
    production_cove_project: str = ""


settings = Settings()
