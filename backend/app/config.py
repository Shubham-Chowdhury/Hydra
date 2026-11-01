"""Hydra Application Configuration."""

import os
from typing import List


class Settings:
    """Application runtime settings."""

    PROJECT_NAME: str = "Hydra"
    VERSION: str = os.getenv("HYDRA_APP_VERSION", "0.1.0")
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "HYDRA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()

