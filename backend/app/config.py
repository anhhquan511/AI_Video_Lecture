from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str
    DB_NAME: str = "ai_lecture_db"
    SECRET_KEY: str
    GOOGLE_API_KEY: str
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    HUGGINGFACE_API_KEY: str
    SD_PROVIDER: str = "huggingface"
    SD_LOCAL_URL: str = "http://127.0.0.1:7860"
    HUGGINGFACE_API_KEY: str = ""
    # GOOGLE_IMAGE_API_KEY: str = None
    
    class Config:
        env_file = ".env"

settings = Settings()