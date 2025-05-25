# config.py
from pydantic_settings import BaseSettings
from openai import AzureOpenAI
import os

class Settings(BaseSettings):
    # MongoDB settings
    MONGODB_URL: str
    DATABASE_NAME: str = "travel_app"

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-35-turbo"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"

    class Config:
        # Load environment variables from .env file in development
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow overriding via OS environment variables in production
        case_sensitive = True

# Instantiate settings (reads from .env or environment)
settings = Settings()

# Validate critical settings
required = [
    settings.MONGODB_URL,
    settings.SECRET_KEY,
    settings.AZURE_OPENAI_ENDPOINT,
    settings.AZURE_OPENAI_API_KEY
]
if not all(required):
    missing = [name for name, value in [
        ("MONGODB_URL", settings.MONGODB_URL),
        ("SECRET_KEY", settings.SECRET_KEY),
        ("AZURE_OPENAI_ENDPOINT", settings.AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_API_KEY", settings.AZURE_OPENAI_API_KEY)
    ] if not value]
    raise RuntimeError(f"Missing required configuration(s): {', '.join(missing)}")

class ChatModel:
    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT.rstrip('/')
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        print(f"ChatModel initialized with deployment: {self.deployment_name}")

