"""
Remove Background API Routes

移除背景 + 生成透明视频 + 打包下载

功能：
1. 从视频中提取帧
2. 移除背景
3. 生成透明 WebM 用于前端预览
4. 打包 PNG 序列帧为 ZIP 用于下载
"""

import logging
import zipfile
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import VIDEOS_DIR, FRAMES_DIR, EXPORTS_DIR
from app.services.rmbg import remove_background
from app.services import ffmpeg
from app.agents.ma import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["remove-bg"])


class RemoveBgRequest(BaseModel):
    """Request model for remove background endpoint."""
    session_id: str = Field(..., description="Session ID of the video to process")


class RemoveBgResponse(BaseModel):
    """Response model for remove background endpoint."""
    status: str = Field(..., description="Processing status: completed, failed")
    preview_url: str | None = Field(None, description="URL to transparent WebM for preview")
    download_url: str | None = Field(None, description="URL to download ZIP of PNG frames")
    frame_count: int = Field(..., description="Number of frames processed")
    error: str | None = Field(None, description="Error message if failed")


@router.post("/remove-bg", response_model=RemoveBgResponse)
async def remove_video_background(request: RemoveBgRequest) -> RemoveBgResponse:
    """
    移除背景 + 生成预览 + 打包下载

    Process:
    1. 从 session 获取视频路径
    2. 提取帧并移除背景
    3. 生成透明 WebM 用于前端预览
    4. 打包 PNG 序列帧为 ZIP 用于下载
    """
    session_id = request.session_id

    # 从 session 中获取视频路径
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )

    video_path_str = session.get("video_path")
    if not video_path_str:
        raise HTTPException(
            status_code=404,
            detail=f"No video found in session: {session_id}"
        )

    video_path = Path(video_path_str)
    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found: {video_path}"
        )

    video_id = video_path.stem
    logger.info(f"[remove-bg] 开始处理: {video_path}")

    # 输出目录
    output_dir = FRAMES_DIR / f"{video_id}_rmbg"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: 移除背景
        logger.info(f"[remove-bg] Step 1: 移除背景...")
        processed_frames = await remove_background(
            input_path=str(video_path),
            output_dir=str(output_dir)
        )

        if not processed_frames:
            raise RuntimeError("No processed frames were generated")

        frame_count = len(processed_frames)
        logger.info(f"[remove-bg] ✅ 移除背景完成: {frame_count} 帧")

        # Step 2: 生成透明 WebM 用于预览
        logger.info(f"[remove-bg] Step 2: 生成透明 WebM...")
        processed_dir = output_dir / "processed"
        webm_path = output_dir / "preview.webm"

        await ffmpeg.create_video_from_frames(
            frame_dir=str(processed_dir),
            output_path=str(webm_path),
            fps=24,
            codec="libvpx-vp9",
            pixel_format="yuva420p"
        )

        preview_url = f"/frames/{video_id}_rmbg/preview.webm"
        logger.info(f"[remove-bg] ✅ WebM 生成完成: {preview_url}")

        # Step 3: 打包 ZIP 用于下载
        logger.info(f"[remove-bg] Step 3: 打包 ZIP...")
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = EXPORTS_DIR / f"{video_id}_frames.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for frame_path in processed_frames:
                frame_file = Path(frame_path)
                zf.write(frame_path, frame_file.name)

        download_url = f"/exports/{video_id}_frames.zip"
        logger.info(f"[remove-bg] ✅ ZIP 打包完成: {download_url}")

        return RemoveBgResponse(
            status="completed",
            preview_url=preview_url,
            download_url=download_url,
            frame_count=frame_count
        )

    except FileNotFoundError as e:
        logger.error(f"[remove-bg] 文件未找到: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"[remove-bg] 处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"[remove-bg] 意外错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Background removal failed: {str(e)}"
        )


@router.get("/remove-bg/status/{session_id}")
async def get_remove_bg_status(session_id: str) -> Dict[str, Any]:
    """检查移除背景是否已完成"""
    session = get_session(session_id)
    if not session:
        return {"exists": False, "frame_count": 0}

    video_path_str = session.get("video_path")
    if not video_path_str:
        return {"exists": False, "frame_count": 0}

    video_id = Path(video_path_str).stem
    output_dir = FRAMES_DIR / f"{video_id}_rmbg"

    if not output_dir.exists():
        return {"exists": False, "frame_count": 0}

    # 检查是否有预览文件
    preview_path = output_dir / "preview.webm"
    preview_url = f"/frames/{video_id}_rmbg/preview.webm" if preview_path.exists() else None

    # 统计帧数
    processed_dir = output_dir / "processed"
    frame_count = len(list(processed_dir.glob("*.png"))) if processed_dir.exists() else 0

    return {
        "exists": True,
        "frame_count": frame_count,
        "preview_url": preview_url,
        "download_url": f"/exports/{video_id}_frames.zip"
    }
