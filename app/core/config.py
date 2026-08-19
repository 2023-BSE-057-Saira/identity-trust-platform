import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://idtrust:idtrust_dev_pw@localhost:5432/idtrust_db",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ENV: str = os.getenv("ENV", "development")

    FACE_MATCH_THRESHOLD: float = float(os.getenv("FACE_MATCH_THRESHOLD", 0.55))
    BLINK_EAR_THRESHOLD: float = float(os.getenv("BLINK_EAR_THRESHOLD", 0.21))
    BLINK_CONSEC_FRAMES: int = int(os.getenv("BLINK_CONSEC_FRAMES", 2))


settings = Settings()
