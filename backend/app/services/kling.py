"""
Kling AI Video Generation Service

封装可灵 AI 图生视频 API，提供异步接口调用、任务轮询和视频下载功能。
支持 Mock 模式用于开发测试。

API 文档: https://app.klingai.com/cn/dev/document-api/apiReference/model/textToVideo
"""

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
import jwt
from ..config import KLING_ACCESS_KEY, KLING_SECRET_KEY, VIDEOS_DIR

logger = logging.getLogger(__name__)

# 可灵官方 API 接入点
KLING_API_BASE_URL = "https://api-beijing.klingai.com"
KLING_VIDEOS_ENDPOINT = f"{KLING_API_BASE_URL}/v1/videos/image2video"

# 支持的模型列表
SUPPORTED_MODELS = [
    "kling-v1",        # V1 模型
    "kling-v1-5",      # V1.5 模型
    "kling-v2",        # V2 模型
    "kling-v2-1",      # V2.1 模型
    "kling-v2-5-turbo",# V2.5 Turbo
    "kling-v2-6",      # V2.6 模型
    "kling-v3",        # V3 模型
]

# 默认模型 (使用 kling-v1-5 平衡性价比和速度)
DEFAULT_MODEL = "kling-v1-5"

# 轮询间隔（秒）
POLL_INTERVAL = 5

# 轮询最大次数（避免无限循环，5秒 * 120次 = 10分钟超时）
MAX_POLL_ATTEMPTS = 120

# Token 缓存（避免频繁生成导致签名无效）
_cached_token: Optional[str] = None
_token_expiry: float = 0


def _get_cached_token() -> str:
    """
    获取缓存的 JWT Token，如果过期则重新生成

    Returns:
        JWT Token 字符串
    """
    global _cached_token, _token_expiry

    now = time.time()

    # 如果 Token 不存在或即将过期（提前5分钟刷新），则重新生成
    if _cached_token is None or now >= _token_expiry - 300:
        # 调试：检查 API Key 配置
        if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
            logger.error("Kling API Keys not configured! Check KLING_ACCESS_KEY and KLING_SECRET_KEY")
        else:
            logger.debug(f"Generating token with ACCESS_KEY length: {len(KLING_ACCESS_KEY)}, SECRET_KEY length: {len(KLING_SECRET_KEY)}")

        _cached_token = _generate_jwt_token()
        _token_expiry = now + 3600  # 1小时有效期
        logger.debug("Generated new JWT token")

    return _cached_token


def is_mock_mode() -> bool:
    """检查是否启用 Mock 模式（无 API Key 时）"""
    return not KLING_ACCESS_KEY or not KLING_SECRET_KEY


def _generate_jwt_token(exp_seconds: int = 3600) -> str:
    """
    生成可灵 AI API JWT Token

    Args:
        exp_seconds: 过期时间（秒），默认1小时

    Returns:
        JWT Token 字符串
    """
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }

    now = int(time.time())
    payload = {
        "iss": KLING_ACCESS_KEY,
        "iat": now,
        "exp": now + exp_seconds,
        "nbf": now - 5  # Not before: 5 seconds ago to allow clock skew
    }

    token = jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256", headers=headers)
    return token


def _encode_image_to_base64(image_path: str) -> str:
    """
    将本地图片文件编码为 Base64 字符串

    Args:
        image_path: 图片文件路径

    Returns:
        Base64 编码的字符串（不含前缀）

    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 图片格式不支持或文件过大
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # 检查文件大小（API 限制 10MB）
    file_size = path.stat().st_size
    if file_size > 10 * 1024 * 1024:
        raise ValueError(f"Image file too large (max 10MB): {file_size} bytes")

    # 检查图片格式
    supported_formats = {".jpg", ".jpeg", ".png"}
    if path.suffix.lower() not in supported_formats:
        raise ValueError(f"Unsupported image format: {path.suffix}. Supported: {supported_formats}")

    # 读取并编码
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return encoded


async def _make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs
) -> Dict[str, Any]:
    """
    发起 HTTP 请求的辅助函数

    Args:
        client: httpx 异步客户端
        method: HTTP 方法
        url: 请求 URL
        **kwargs: 其他 httpx 请求参数

    Returns:
        响应 JSON 数据

    Raises:
        httpx.HTTPError: 请求失败
    """
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {_get_cached_token()}"  # 使用缓存的 Token
    headers["Content-Type"] = "application/json"

    logger.info(f"[Kling] 请求: {method} {url}")

    try:
        response = await client.request(method, url, headers=headers, **kwargs)
    except httpx.ConnectError as e:
        logger.error(f"[Kling] 连接失败 (DNS/网络问题): {e}")
        raise
    except Exception as e:
        logger.error(f"[Kling] 请求异常: {type(e).__name__}: {e}")
        raise

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # 详细打印错误响应以便调试
        logger.error(f"Kling API request failed: {e.response.status_code}")
        logger.error(f"Response body: {e.response.text}")
        try:
            error_json = e.response.json()
            logger.error(f"Error details: {error_json}")
        except Exception:
            pass
        raise

    logger.info(f"[Kling] 响应状态: {response.status_code}")
    return response.json()


async def image_to_video(
    image_path: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    seconds: str = "5",
    size: str = "1920x1080",
    mode: str = "std",
    tail_image_path: Optional[str] = None
) -> str:
    """
    提交图生视频任务

    Args:
        image_path: 输入图片路径（首帧）
        prompt: 视频生成提示词
        model: 使用的模型，默认 kling-video-o1
        seconds: 视频时长，"5" 或 "10"
        size: 视频分辨率，如 "1920x1080"
        mode: 生成模式，"std" (720P) 或 "pro" (1080P)
        tail_image_path: 尾帧图片路径（可选，用于首尾帧控制）

    Returns:
        任务 ID

    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 参数无效
        httpx.HTTPError: API 请求失败
    """
    if is_mock_mode():
        logger.info("Mock mode: Returning fake task ID")
        return "mock-task-id-12345"

    # 验证模型
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    # 验证参数
    if seconds not in ["5", "10"]:
        raise ValueError("seconds must be '5' or '10'")

    if mode not in ["std", "pro"]:
        raise ValueError("mode must be 'std' or 'pro'")

    # 如果指定了尾帧，必须是 pro 模式
    if tail_image_path and mode != "pro":
        raise ValueError("Tail frame requires mode='pro'")

    # 编码图片
    image_base64 = _encode_image_to_base64(image_path)

    # 构建请求体 (官方 API 字段名)
    request_body: Dict[str, Any] = {
        "model_name": model,     # 官方 API 使用 model_name
        "prompt": prompt,
        "image": image_base64,   # 官方 API 使用 "image" 字段
        "duration": seconds,     # 官方 API 使用 "duration" 字段
        "mode": mode,            # std 或 pro
        "cfg_scale": 0.5,        # 创意自由度
    }

    # 添加尾帧（首尾帧控制）
    if tail_image_path:
        tail_base64 = _encode_image_to_base64(tail_image_path)
        request_body["image_tail"] = tail_base64  # 官方字段名

    logger.info(f"Submitting image-to-video task with model={model}, mode={mode}, seconds={seconds}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await _make_request(
            client,
            "POST",
            KLING_VIDEOS_ENDPOINT,
            json=request_body
        )

    # 官方 API 返回格式: {"data": {"task_id": "...", "task_status": "..."}}
    data = response.get("data", {})
    task_id = data.get("task_id")
    if not task_id:
        raise ValueError(f"Invalid API response: missing task ID. Response: {response}")

    logger.info(f"Task submitted successfully. Task ID: {task_id}")
    return task_id


async def poll_task(task_id: str) -> Dict[str, Any]:
    """
    轮询查询任务状态直到完成

    Args:
        task_id: 任务 ID

    Returns:
        任务结果字典，包含任务状态和视频信息

    Raises:
        httpx.HTTPError: API 请求失败
        TimeoutError: 轮询超时
    """
    if is_mock_mode():
        logger.info(f"  [Kling] Mock 模式: 模拟任务完成")
        # 模拟延迟，模拟异步处理
        await asyncio.sleep(2)
        return {
            "data": {
                "task_id": task_id,
                "task_status": "succeed",
                "task_result": {
                    "videos": [
                        {
                            "id": "mock-video-id",
                            "url": "",  # 由 download_video 处理
                            "duration": "5"
                        }
                    ]
                }
            }
        }

    url = f"{KLING_VIDEOS_ENDPOINT}/{task_id}"
    attempt = 0
    last_status = None

    while attempt < MAX_POLL_ATTEMPTS:
        attempt += 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await _make_request(client, "GET", url)

        # 官方 API 返回格式: {"data": {"task_status": "...", "task_result": {...}}}
        data = response.get("data", {})
        status = data.get("task_status", "unknown")

        # 只在状态变化时输出日志
        if status != last_status:
            logger.info(f"  [Kling] 状态变更: {last_status or '初始'} → {status}")
            last_status = status

        # 显示进度
        progress = min(100, int(attempt / MAX_POLL_ATTEMPTS * 100))
        if attempt % 6 == 0:  # 每30秒输出一次进度
            logger.info(f"  [Kling] 等待中... ({attempt}/{MAX_POLL_ATTEMPTS}, {progress}%)")

        # 检查是否完成 (官方 API 使用 "succeed")
        if status == "succeed":
            logger.info(f"  [Kling] ✅ 任务完成: {task_id}")
            return response

        if status == "failed":
            error_msg = data.get("task_status_msg", "Unknown error")
            logger.error(f"  [Kling] ❌ 任务失败: {error_msg}")
            raise ValueError(f"Task failed: {error_msg}")

        # 继续轮询
        await asyncio.sleep(POLL_INTERVAL)

    logger.error(f"  [Kling] ⏱️ 轮询超时")
    raise TimeoutError(f"Task polling timeout after {MAX_POLL_ATTEMPTS * POLL_INTERVAL} seconds")


async def download_video(video_url: str, output_path: Optional[str] = None) -> str:
    """
    下载生成的视频到本地

    Args:
        video_url: 视频 URL
        output_path: 输出路径（可选，默认自动生成）

    Returns:
        本地视频文件路径

    Raises:
        httpx.HTTPError: 下载失败
    """
    if is_mock_mode():
        # Mock 模式：使用预置测试视频
        mock_video_path = VIDEOS_DIR / "mock_test_video.mp4"
        if not mock_video_path.exists():
            # Create a minimal valid MP4 file for development testing
            # This is a tiny but valid MP4 with 1 black frame (avoids ffmpeg errors)
            import subprocess
            VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y", "-f", "lavfi", "-i",
                    "color=c=black:s=320x240:d=1:r=24",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(mock_video_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode != 0:
                    # Fallback: write empty bytes (better than text)
                    mock_video_path.write_bytes(b"")
            except FileNotFoundError:
                # ffmpeg not available, write empty file
                mock_video_path.write_bytes(b"")
            logger.warning(f"Created mock video file: {mock_video_path}")
        return str(mock_video_path)

    # 生成输出路径
    if output_path is None:
        import time
        output_path = VIDEOS_DIR / f"kling_{asyncio.current_task().get_name() if asyncio.current_task() else 'video'}_{int(time.time())}.mp4"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading video from {video_url} to {output_path}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("GET", video_url) as response:
            response.raise_for_status()

            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

    logger.info(f"Video downloaded successfully: {output_path}")
    return str(output_path)


async def generate_video_from_image(
    image_path: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    seconds: str = "5",
    size: str = "1920x1080",
    mode: str = "std",
    tail_image_path: Optional[str] = None
) -> str:
    """
    完整流程：提交任务 -> 轮询状态 -> 下载视频 -> 返回本地路径

    Args:
        image_path: 输入图片路径
        prompt: 视频生成提示词
        model: 使用的模型
        seconds: 视频时长
        size: 视频分辨率
        mode: 生成模式
        tail_image_path: 尾帧图片路径（可选）

    Returns:
        本地视频文件路径
    """
    logger.info("=" * 50)
    logger.info("  🎬 Kling AI 视频生成流程")
    logger.info("=" * 50)

    # Step 1: 提交任务
    logger.info("  [Kling] Step 1/3: 提交图生视频任务...")
    logger.info(f"         model={model}, mode={mode}, duration={seconds}s")

    task_id = await image_to_video(
        image_path=image_path,
        prompt=prompt,
        model=model,
        seconds=seconds,
        size=size,
        mode=mode,
        tail_image_path=tail_image_path
    )
    logger.info(f"  [Kling] ✅ 任务已提交: task_id={task_id}")

    # Step 2: 轮询任务状态
    logger.info("  [Kling] Step 2/3: 等待视频生成...")
    result = await poll_task(task_id)

    # Step 3: 下载视频
    logger.info("  [Kling] Step 3/3: 下载视频...")

    if is_mock_mode():
        local_path = await download_video("")
        logger.info(f"  [Kling] ✅ Mock 视频已生成: {local_path}")
        logger.info("=" * 50)
        return local_path

    # 官方 API 返回格式: {"data": {"task_result": {"videos": [...]}}}
    data = result.get("data", {})
    videos = data.get("task_result", {}).get("videos", [])
    if not videos:
        raise ValueError(f"No video in task result: {result}")

    video_url = videos[0].get("url")
    if not video_url:
        raise ValueError(f"No video URL in result: {videos[0]}")

    local_path = await download_video(video_url)
    logger.info(f"  [Kling] ✅ 视频已下载: {local_path}")
    logger.info("=" * 50)

    return local_path


async def text_to_video(
    prompt: str,
    model: str = DEFAULT_MODEL,
    seconds: str = "5",
    size: str = "1920x1080",
    mode: str = "std"
) -> str:
    """
    文生视频（仅 kling-video-o1 和 kling-v2-5-turbo 支持）

    TODO: 此功能需要 API 支持，当前 API 文档中图生视频必须提供 input_reference
    文生视频可能需要不同的参数或接口

    Args:
        prompt: 文本提示词
        model: 使用的模型
        seconds: 视频时长
        size: 视频分辨率
        mode: 生成模式

    Returns:
        本地视频文件路径
    """
    # TODO: 根据实际 API 文档实现文生视频功能
    raise NotImplementedError(
        "Text-to-video is not yet implemented. "
        "Please refer to the latest Kling API documentation for text-to-video support."
    )
