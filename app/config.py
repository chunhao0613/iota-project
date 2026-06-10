import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = "sqlite:///./data/iot_data.db"
    
    # IOTA node configuration
    # Defaulting to Shimmer network L1 node for absolute public node stability
    IOTA_NODE_URL: str = "https://api.shimmer.network"
    IOTA_TAG: str = "IOT_DATA_INTEGRITY_DEMO"
    
    # Server configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global settings instance
settings = Settings()

# Ensure the database directory exists
db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)
