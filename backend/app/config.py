import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Google Cloud Configuration
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Firebase Configuration
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/tripplanner")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Payment Configuration
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Application Configuration
    app_name: str = os.getenv("APP_NAME", "AI Trip Planner")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # EMT Booking API
    emt_api_base_url: str = os.getenv("EMT_API_BASE_URL", "https://api.emt-booking.com")
    emt_api_key: str = os.getenv("EMT_API_KEY", "")
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:8501", "http://localhost:3000", "*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()