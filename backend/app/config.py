from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- 项目 ---
    PROJECT_NAME: str = "植物病害识别系统"
    DEBUG: bool = False

    # --- 路径 ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent  # ResNet/
    MODEL_PATH: Optional[str] = None  # 为空则自动定位
    DATASET_DIR: Optional[str] = None
    UPLOAD_DIR: Optional[str] = None

    # --- 数据库 ---
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "plant_disease"
    DATABASE_URL: Optional[str] = None

    # --- JWT ---
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # --- 推理 ---
    TOP_K: int = 5
    MAX_TOP_K: int = 20
    MAX_BATCH_SIZE: int = 10

    @property
    def model_path(self) -> Path:
        if self.MODEL_PATH:
            return Path(self.MODEL_PATH)
        return self.BASE_DIR / "resnet50_阶段二_(全局微调)_best.pth"

    @property
    def dataset_dir(self) -> Path:
        if self.DATASET_DIR:
            return Path(self.DATASET_DIR)
        return self.BASE_DIR / "datasets" / "color"

    @property
    def upload_dir(self) -> Path:
        if self.UPLOAD_DIR:
            return Path(self.UPLOAD_DIR)
        return self.BASE_DIR / "uploads"

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {
        "env_file": [
            Path(__file__).resolve().parent.parent / ".env",  # backend/.env
            ".env",  # CWD/.env
        ],
        "env_file_encoding": "utf-8",
    }


settings = Settings()
