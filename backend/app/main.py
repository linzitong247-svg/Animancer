import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import generate, removebg, export
from app.config import VIDEOS_DIR, FRAMES_DIR, UPLOADS_DIR, EXPORTS_DIR

# 配置日志 - 必须在导入其他模块之前
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置第三方库日志级别
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("🚀 Animancer API 启动中...")

app = FastAPI(title="Animancer API", version="0.1.0")

# 挂载静态文件目录 - 让视频可以通过 HTTP 访问
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")
app.mount("/frames", StaticFiles(directory=str(FRAMES_DIR)), name="frames")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")
logger.info(f"📁 静态文件服务已挂载: /videos, /frames, /uploads, /exports")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generate.router)
app.include_router(removebg.router)
app.include_router(export.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
