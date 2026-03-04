"""
LLM Service - 智谱 AI API 封装

提供异步聊天接口，支持纯文本和多模态（图片）调用。
遵循 FastAPI 最佳实践：async/await、类型注解、错误处理。
"""

from openai import AsyncOpenAI
from typing import Optional, List
import logging

from ..config import ZHIPU_API_KEY

logger = logging.getLogger(__name__)

# 异步 OpenAI 客户端，配置智谱端点
client = AsyncOpenAI(
    api_key=ZHIPU_API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)


async def chat(
    system_prompt: str,
    user_message: str,
    image_url: Optional[str] = None,
    image_urls: Optional[List[str]] = None
) -> str:
    """
    调用智谱 AI 进行对话

    Args:
        system_prompt: 系统提示词，设定 AI 行为和角色
        user_message: 用户消息内容
        image_url: 可选的单张图片 URL，传入时使用多模态模型
        image_urls: 可选的多张图片 URL 列表，传入时使用多模态模型

    Returns:
        str: AI 返回的回复内容

    Raises:
        ValueError: API Key 未配置或参数无效
        TimeoutError: 请求超时
        RuntimeError: API 调用失败（限频、服务错误等）
    """
    if not ZHIPU_API_KEY:
        raise ValueError("ZHIPU_API_KEY 未配置，请检查环境变量")

    if not user_message:
        raise ValueError("user_message 不能为空")

    # 合并 image_url 和 image_urls
    all_images = list(image_urls or [])
    if image_url and image_url not in all_images:
        all_images.insert(0, image_url)

    has_images = len(all_images) > 0

    # 根据是否包含图片选择模型
    model = "glm-4v-flash" if has_images else "glm-4-flash"

    # 构建消息列表
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if has_images:
        # 多模态消息：文本 + 多张图片
        content = [{"type": "text", "text": user_message}]
        for img_url in all_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": img_url}
            })
        messages.append({"role": "user", "content": content})
    else:
        # 纯文本消息
        messages.append({
            "role": "user",
            "content": user_message
        })

    try:
        logger.info(f"调用 LLM: model={model}, images={len(all_images)}")

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=30.0,  # 30 秒超时
        )

        if not response.choices:
            raise RuntimeError("LLM 返回空响应（无 choices）")
        result = response.choices[0].message.content or ""
        logger.info(f"LLM 响应成功: {len(result)} 字符")
        return result

    except TimeoutError as e:
        logger.error(f"LLM 请求超时: {e}")
        raise TimeoutError("LLM 服务响应超时，请稍后重试") from e

    except Exception as e:
        error_msg = str(e)

        # 处理常见错误类型
        if "rate limit" in error_msg.lower():
            logger.error(f"LLM 限频: {e}")
            raise RuntimeError("API 调用频率超限，请稍后重试") from e

        if "401" in error_msg or "unauthorized" in error_msg.lower():
            logger.error(f"LLM 认证失败: {e}")
            raise ValueError("API Key 无效或已过期") from e

        if "429" in error_msg:
            logger.error(f"LLM 配额超限: {e}")
            raise RuntimeError("API 配额已用完") from e

        # 其他未预期的错误
        logger.error(f"LLM 调用失败: {e}")
        raise RuntimeError(f"LLM 服务异常: {error_msg}") from e
