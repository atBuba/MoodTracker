from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # LLM model (sentiment, productivity, mood analysis, meme captions)
    openrouter_llm_model: str = "google/gemini-3-flash-preview"
    openrouter_max_tokens: int = 4096

    # Image generation model (memes)
    openrouter_image_model: str = "sourceful/riverflow-v2-pro"

    internal_api_key: str = ""

    minio_url: str = "http://minio:9000"
    minio_user: str = "minioadmin"
    minio_password: str = "changeme"

    backend_url: str = "http://backend:8000"
    rabbitmq_url: str = "amqp://burnoutdetector:changeme@rabbitmq:5672/"

    prompts_dir: Path = Path(__file__).parent / "prompts"


settings = Settings()
