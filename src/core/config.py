from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_vision_model: str = "moondream"
    vision_timeout: int = 60

    class Config:
        env_file = ".env"

cfg = AppSettings()
