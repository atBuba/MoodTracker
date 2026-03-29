from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backend integration
    INTERNAL_API_KEY: str = "your-internal-api-key"
    BACKEND_URL: str = "http://backend:8000"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://burnoutdetector:changeme@rabbitmq:5672/"

    # Mock data generation interval (minutes)
    MOCK_INTERVAL_MINUTES: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
