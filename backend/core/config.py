import os

class Settings:
    # API key and URL configurations
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    
    # Model Configurations
    GROQ_MODEL: str = "llama3-8b-8192"
    GROQ_FALLBACK_MODELS: list = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768"
    ]
    
    # Scoring calculation weights
    LLM_CONFIDENCE_WEIGHT: float = 0.6
    STATIC_CONFIDENCE_WEIGHT: float = 0.4

settings = Settings()
