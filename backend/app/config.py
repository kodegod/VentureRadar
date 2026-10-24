from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://ventureradar:ventureradar@localhost:5432/ventureradar"
    redis_url: str = "redis://localhost:6379/0"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_extract_model: str = "gpt-4.1-mini"
    llm_eval_model: str = "gpt-4.1"
    embedding_model: str = "text-embedding-3-small"

    tavily_api_key: str = ""

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_username: str = ""
    reddit_password: str = ""
    reddit_user_agent: str = "web:ventureradar:0.1.0 (by /u/unknown)"

    x_bearer_token: str = ""

    budget_llm_daily: float = 5.0
    budget_llm_monthly: float = 30.0
    budget_tavily_daily: float = 1.0
    budget_tavily_monthly: float = 8.0
    budget_x_daily: float = 2.0
    budget_x_monthly: float = 20.0

    research_paused: bool = False
    live_collection_enabled: bool = False

    scoring_version: str = "2"
    threshold_version: str = "1"


settings = Settings()
