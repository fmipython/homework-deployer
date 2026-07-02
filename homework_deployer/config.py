from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    staging_repo: str = ""
    production_repo: str = ""
    cove_url: str = ""
    cove_api_key: str = ""
    cove_project: str = ""
