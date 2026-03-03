"""
Sub-Agent G (SA_G) - Animation Generation Agent

负责调用 Kling AI 图生视频服务，生成动画视频文件。
"""

import logging
from pathlib import Path
from ..services import kling
from ..config import VIDEOS_DIR

logger = logging.getLogger(__name__)


async def generate_animation(image_path: str, prompt: str) -> str:
    """
    Generate an animation video from a static image using Kling AI.

    This agent wraps the Kling image-to-video service, handling the
    orchestration of submitting the task and retrieving the result.

    Args:
        image_path: Absolute path to the input image file
        prompt: Optimized English prompt for the animation generation

    Returns:
        str: Absolute path to the generated video file

    Raises:
        FileNotFoundError: If the input image file does not exist
        ValueError: If image_path or prompt is empty
        RuntimeError: If the video generation process fails

    Example:
        >>> video_path = await generate_animation(
        ...     image_path="/path/to/character.png",
        ...     prompt="The character waves their hand gently"
        ... )
        >>> print(video_path)
        "/path/to/data/videos/generated_video.mp4"
    """
    logger.info("  🔹 [SA_G] 调用 Kling AI 生成动画...")

    if not image_path:
        raise ValueError("image_path cannot be empty")

    if not prompt:
        raise ValueError("prompt cannot be empty")

    # Validate input image exists
    image_file = Path(image_path)
    if not image_file.exists():
        logger.error(f"  🔹 [SA_G] ❌ 输入图片不存在: {image_path}")
        raise FileNotFoundError(f"Input image not found: {image_path}")

    logger.info(f"    输入图片: {image_file.name} ({image_file.stat().st_size} bytes)")
    logger.info(f"    Prompt: {prompt[:80]}...")

    # Ensure videos directory exists
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Call Kling AI service (full pipeline: submit -> poll -> download)
        video_path = await kling.generate_video_from_image(
            image_path=image_path,
            prompt=prompt
        )

        # Validate the returned video path
        if not video_path:
            raise RuntimeError("Kling service returned empty video path")

        video_file = Path(video_path)
        if not video_file.exists():
            raise RuntimeError(f"Generated video file not found: {video_path}")

        video_size = video_file.stat().st_size
        logger.info(f"  🔹 [SA_G] ✅ 视频生成成功: {video_file.name} ({video_size} bytes)")
        return str(video_file.absolute())

    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"  🔹 [SA_G] ❌ 动画生成失败: {type(e).__name__}: {e}")
        raise RuntimeError(f"Failed to generate animation: {e}") from e
