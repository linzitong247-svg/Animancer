"""
Export API Routes

Provides endpoints for exporting generated animations:
- POST /api/export-png - Export frames as downloadable ZIP
- GET /api/export/{id} - Export video or frames as downloadable ZIP
"""

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import VIDEOS_DIR, FRAMES_DIR, EXPORTS_DIR
from app.services.ffmpeg import frames_to_zip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["export"])


class ExportPngRequest(BaseModel):
    """Request model for export PNG endpoint."""
    session_id: str = Field(..., description="Session ID of the video to export")


class ExportPngResponse(BaseModel):
    """Response model for export PNG endpoint."""
    status: str = Field(..., description="Export status")
    download_url: str = Field(..., description="URL to download the ZIP file")
    frame_count: int = Field(..., description="Number of frames exported")


@router.post("/export-png", response_model=ExportPngResponse)
async def export_png_frames(request: ExportPngRequest) -> ExportPngResponse:
    """
    Export extracted frames as a downloadable ZIP file.

    Args:
        request: Contains session_id of the video

    Returns:
        ExportPngResponse with download URL
    """
    video_id = request.session_id

    # 查找已提取的帧目录
    frames_dir = FRAMES_DIR / video_id
    if not frames_dir.exists():
        # 尝试查找去背景的帧
        frames_dir = FRAMES_DIR / f"{video_id}_rmbg"
        if not frames_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Frames not found for session: {video_id}"
            )

    # 统计帧数
    frame_files = list(frames_dir.glob("**/*.png"))
    frame_count = len(frame_files)

    if frame_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No frames found in: {frames_dir}"
        )

    # 创建 ZIP 文件
    zip_filename = f"{video_id}_frames.zip"
    zip_path = EXPORTS_DIR / zip_filename
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    await frames_to_zip(str(frames_dir), str(zip_path))

    return ExportPngResponse(
        status="completed",
        download_url=f"/exports/{zip_filename}",
        frame_count=frame_count
    )


@router.post("/export-video")
async def export_video_file(request: ExportPngRequest) -> dict:
    """
    Export the generated video file.

    Args:
        request: Contains session_id of the video

    Returns:
        Dict with video URL
    """
    video_id = request.session_id

    # Search for video files matching the video_id
    video_files = list(VIDEOS_DIR.glob(f"*{video_id}*.mp4")) + list(VIDEOS_DIR.glob(f"*{video_id}*.mov"))
    if not video_files:
        # Also try direct filename
        direct_path = VIDEOS_DIR / f"{video_id}.mp4"
        if direct_path.exists():
            video_files = [direct_path]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No video file found for session: {video_id}"
            )

    video_path = video_files[0]
    video_url = f"/videos/{video_path.name}"

    return {
        "status": "completed",
        "video_url": video_url,
        "filename": video_path.name
    }


@router.get("/{video_id}")
async def export_video(
    video_id: str,
    format: Literal["video", "frames", "rmbg_frames"] = "video"
) -> FileResponse:
    """
    Export a generated video or frames as a downloadable file.

    Args:
        video_id: ID of the video to export (typically session_id)
        format: Export format:
            - "video": Original video file (mp4/mov)
            - "frames": ZIP archive of extracted frames
            - "rmbg_frames": ZIP archive of background-removed frames

    Returns:
        FileResponse with appropriate content-type and headers

    Raises:
        HTTPException: 404 if content not found, 500 if export fails
    """
    if format == "video":
        # Export original video (flat file structure)
        video_files = list(VIDEOS_DIR.glob(f"*{video_id}*.mp4")) + list(VIDEOS_DIR.glob(f"*{video_id}*.mov"))
        if not video_files:
            direct_path = VIDEOS_DIR / f"{video_id}.mp4"
            if direct_path.exists():
                video_files = [direct_path]
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"No video file found for video_id: {video_id}"
                )

        video_path = video_files[0]
        media_type = "video/mp4" if video_path.suffix == ".mp4" else "video/quicktime"

        return FileResponse(
            path=str(video_path),
            media_type=media_type,
            filename=f"{video_id}{video_path.suffix}",
            background=None
        )

    elif format == "frames":
        # Export frames as ZIP
        frames_dir = FRAMES_DIR / video_id

        if not frames_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Frames directory not found: {video_id}"
            )

        # Create ZIP file
        zip_path = EXPORTS_DIR / f"{video_id}_frames.zip"
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        await frames_to_zip(str(frames_dir), str(zip_path))

        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=f"{video_id}_frames.zip",
            background=None
        )

    elif format == "rmbg_frames":
        # Export background-removed frames as ZIP
        frames_dir = FRAMES_DIR / f"{video_id}_rmbg"

        if not frames_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Background-removed frames not found for video_id: {video_id}"
            )

        # Create ZIP file
        zip_path = EXPORTS_DIR / f"{video_id}_rmbg_frames.zip"
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        await frames_to_zip(str(frames_dir), str(zip_path))

        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=f"{video_id}_rmbg_frames.zip",
            background=None
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {format}. Must be 'video', 'frames', or 'rmbg_frames'"
        )


@router.get("/{video_id}/info")
async def get_export_info(video_id: str) -> dict:
    """
    Get information about available export formats for a video.

    Args:
        video_id: ID of the video to query

    Returns:
        Dictionary with available formats and their status

    Raises:
        HTTPException: 500 if query fails
    """
    frames_dir = FRAMES_DIR / video_id
    rmbg_frames_dir = FRAMES_DIR / f"{video_id}_rmbg"

    # Check video (flat file structure)
    video_files = list(VIDEOS_DIR.glob(f"*{video_id}*.mp4")) + list(VIDEOS_DIR.glob(f"*{video_id}*.mov"))

    # Check frames
    frame_count = 0
    if frames_dir.exists():
        frame_count = len(list(frames_dir.glob("*.png")))

    # Check background-removed frames
    rmbg_frame_count = 0
    if rmbg_frames_dir.exists():
        rmbg_frame_count = len(list(rmbg_frames_dir.glob("*.png")))

    return {
        "video_id": video_id,
        "available_formats": {
            "video": len(video_files) > 0,
            "frames": frame_count > 0,
            "rmbg_frames": rmbg_frame_count > 0
        },
        "details": {
            "video_exists": len(video_files) > 0,
            "video_path": str(video_files[0]) if video_files else None,
            "frame_count": frame_count,
            "rmbg_frame_count": rmbg_frame_count
        }
    }
