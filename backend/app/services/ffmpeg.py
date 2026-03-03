# FFmpeg service - handles video processing

import asyncio
import logging
import subprocess
import zipfile
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_thread_pool = ThreadPoolExecutor(max_workers=4)


async def _run_command_async(cmd: List[str], timeout: int = 60) -> tuple[int, bytes, bytes]:
    """
    异步执行命令，兼容 Windows 和其他平台。

    使用 asyncio.to_thread 包装同步的 subprocess.run，避免 Windows 上的事件循环问题。

    Args:
        cmd: 命令和参数列表
        timeout: 超时时间（秒）

    Returns:
        (returncode, stdout, stderr) 元组
    """
    def _run_sync():
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_thread_pool, _run_sync)


def get_ffmpeg_path() -> str:
    """获取 ffmpeg 可执行文件路径"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        logger.warning("imageio-ffmpeg not installed, using system ffmpeg")
        return "ffmpeg"


def get_ffprobe_path() -> str:
    """获取 ffprobe 可执行文件路径"""
    # imageio-ffmpeg 只提供 ffmpeg，不提供 ffprobe
    # 我们将使用 ffmpeg -i 来获取视频信息
    return get_ffmpeg_path()  # 使用 ffmpeg 代替 ffprobe


FFMPEG_PATH = get_ffmpeg_path()
FFPROBE_PATH = get_ffprobe_path()
logger.info(f"FFmpeg paths: ffmpeg={FFMPEG_PATH}, ffprobe替代={FFPROBE_PATH}")


async def extract_frames(
    video_path: str,
    output_dir: str,
    fps: int = 24,
    pattern: str = "frame_%06d.png"
) -> List[str]:
    """
    Extract frames from a video file using ffmpeg.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory where extracted frames will be saved.
        fps: Frames per second for extraction (default: 24).
        pattern: Output filename pattern for frames (default: "frame_%06d.png").

    Returns:
        List of paths to extracted frame files.

    Raises:
        RuntimeError: If ffmpeg execution fails.
    """
    video_file = Path(video_path)
    output_path = Path(output_dir)

    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    output_pattern = output_path / pattern

    # Build ffmpeg command
    cmd = [
        FFMPEG_PATH,
        "-i", str(video_file),
        "-vf", f"fps={fps}",
        "-vsync", "0",
        "-q:v", "1",  # High quality
        "-y",  # Overwrite output files
        str(output_pattern)
    ]

    # Run ffmpeg using thread pool (Windows-compatible)
    returncode, stdout, stderr = await _run_command_async(cmd, timeout=300)

    if returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg failed: {error_msg}")

    # Collect all extracted frames
    frame_files = sorted(output_path.glob("frame_*.png"))
    return [str(f) for f in frame_files]


async def frames_to_zip(frame_dir: str, output_path: str) -> str:
    """
    Pack all PNG frames from a directory into a ZIP archive.

    Args:
        frame_dir: Directory containing PNG frame files.
        output_path: Path where the ZIP file will be created.

    Returns:
        Path to the created ZIP file.

    Raises:
        RuntimeError: If zipping operation fails.
    """
    frames_path = Path(frame_dir)
    zip_path = Path(output_path)

    if not frames_path.exists():
        raise FileNotFoundError(f"Frames directory not found: {frame_dir}")

    # Get all PNG files, sorted
    frame_files = sorted(frames_path.glob("*.png"))

    if not frame_files:
        raise RuntimeError(f"No PNG files found in {frame_dir}")

    # Run zip creation in thread pool to avoid blocking
    def _create_zip() -> str:
        try:
            # Ensure output directory exists
            zip_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(
                zip_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=6
            ) as zf:
                for frame_file in frame_files:
                    # Store files with just the filename (no directory structure)
                    zf.write(frame_file, arcname=frame_file.name)

            return str(zip_path)
        except Exception as e:
            raise RuntimeError(f"Failed to create ZIP archive: {e}")

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_thread_pool, _create_zip)


async def get_video_info(video_path: str) -> dict:
    """
    Get video metadata including duration, fps, resolution.
    使用 ffmpeg -i 代替 ffprobe (imageio-ffmpeg 不提供 ffprobe)

    Args:
        video_path: Path to the input video file.

    Returns:
        Dictionary containing video metadata.

    Raises:
        RuntimeError: If ffmpeg execution fails.
    """
    import re

    video_file = Path(video_path)

    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # 使用 ffmpeg -i 获取视频信息 (输出到 stderr)
    cmd = [
        FFMPEG_PATH,
        "-i", str(video_file),
        "-hide_banner"
    ]

    # Run using thread pool (Windows-compatible)
    returncode, stdout, stderr = await _run_command_async(cmd, timeout=30)

    # ffmpeg -i 的输出在 stderr 中
    info_text = stderr.decode("utf-8", errors="replace")
    logger.debug(f"ffmpeg -i output: {info_text[:500]}")

    result = {
        "width": None,
        "height": None,
        "fps": None,
        "duration": None
    }

    # 解析分辨率 (格式: 320x240)
    resolution_match = re.search(r"(\d+)x(\d+)", info_text)
    if resolution_match:
        result["width"] = int(resolution_match.group(1))
        result["height"] = int(resolution_match.group(2))

    # 解析帧率 (格式: 24 fps 或 24 tbr)
    fps_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:fps|tbr)", info_text)
    if fps_match:
        result["fps"] = float(fps_match.group(1))

    # 解析时长 (格式: Duration: 00:00:05.00 或 Duration: 5.000000)
    # 支持两种格式: HH:MM:SS.ms 或 纯秒数
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", info_text)
    if duration_match:
        hours = int(duration_match.group(1))
        minutes = int(duration_match.group(2))
        seconds = float(duration_match.group(3))
        result["duration"] = hours * 3600 + minutes * 60 + seconds
    else:
        # 尝试匹配纯秒数格式
        duration_match = re.search(r"Duration:\s*([\d.]+)", info_text)
        if duration_match:
            result["duration"] = float(duration_match.group(1))

    logger.info(f"Video info extracted: {result}")
    return result


async def create_video_from_frames(
    frame_dir: str,
    output_path: str,
    fps: int = 24,
    codec: str = "prores_ks",
    pixel_format: str = "yuva444p10le"  # Support alpha channel
) -> str:
    """
    Create a video from a sequence of frames using ffmpeg.

    Args:
        frame_dir: Directory containing PNG frame files.
        output_path: Path where the video will be saved.
        fps: Frames per second for output video (default: 24).
        codec: Video codec (default: prores_ks for alpha support).
        pixel_format: Pixel format (default: yuva444p10le for 10-bit 4:4:4:4).

    Returns:
        Path to the created video file.

    Raises:
        RuntimeError: If ffmpeg execution fails.
    """
    frames_path = Path(frame_dir)
    output_file = Path(output_path)

    if not frames_path.exists():
        raise FileNotFoundError(f"Frames directory not found: {frame_dir}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Build input pattern
    input_pattern = frames_path / "frame_%06d.png"

    # Build base command
    cmd = [
        FFMPEG_PATH,
        "-framerate", str(fps),
        "-i", str(input_pattern),
        "-c:v", codec,
        "-pix_fmt", pixel_format,
    ]

    # Add codec-specific parameters
    if codec == "prores_ks":
        # ProRes 4444 supports alpha channel with profile 4
        cmd.extend(["-profile:v", "4"])
    elif codec == "libvpx-vp9":
        # VP9 with alpha: use CRF quality and auto-select profile
        # Profile 3 supports alpha, but let ffmpeg auto-select
        cmd.extend([
            "-crf", "30",           # Quality (lower = better, 0-63)
            "-b:v", "0",            # Use CRF mode
            "-deadline", "realtime", # Faster encoding
            "-cpu-used", "4",       # Speed/quality tradeoff (0-5)
        ])
    elif codec == "libaom-av1":
        # AV1 with alpha
        cmd.extend([
            "-crf", "30",
            "-b:v", "0",
            "-strict", "experimental",
        ])

    cmd.extend(["-y", str(output_file)])

    # Run using thread pool (Windows-compatible)
    returncode, stdout, stderr = await _run_command_async(cmd, timeout=600)

    if returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg video creation failed: {error_msg}")

    return str(output_file)
