import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseModel):
    """Application Settings and Configuration."""
    
    # OmniRouter / Provider Config
    base_url: str = Field(
        default_factory=lambda: os.getenv("OMNIROUTER_BASE_URL", "http://localhost:20128/v1")
    )
    api_key: str = Field(
        default_factory=lambda: os.getenv("OMNIROUTER_API_KEY", "")
    )
    
    # Jev Decision Models
    jev_model: str = Field(
        default_factory=lambda: os.getenv("JEV_MODEL", "openrouter/typesafe/jev-router")
    )
    jev_native_model: str = Field(
        default_factory=lambda: os.getenv("JEV_NATIVE_MODEL", "KloudeKode/typesafe/jev-1.13.0")
    )
    
    # Gemini Specialist Execution Model
    specialist_model: str = Field(
        default_factory=lambda: os.getenv("SPECIALIST_MODEL", "l-s-Poc/gemini-3.7-flash")
    )
    
    # Routing Policy Thresholds
    confidence_threshold_auto: float = Field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD_AUTO", "0.85"))
    )
    confidence_threshold_review: float = Field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD_REVIEW", "0.50"))
    )
    
    # Server Configuration
    server_host: str = Field(
        default_factory=lambda: os.getenv("SERVER_HOST", "0.0.0.0")
    )
    server_port: int = Field(
        default_factory=lambda: int(os.getenv("SERVER_PORT", "8000"))
    )


settings = Settings()
