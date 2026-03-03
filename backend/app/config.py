from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
VIDEOS_DIR = DATA_DIR / "videos"
FRAMES_DIR = DATA_DIR / "frames"
EXPORTS_DIR = DATA_DIR / "exports"

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# 可灵 API 使用 Access Key + Secret Key
KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")

# Ensure data directories exist
for d in [UPLOADS_DIR, VIDEOS_DIR, FRAMES_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
