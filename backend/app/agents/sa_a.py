"""
Sub-Agent A (SA_A) - Animation Prompt Generation Agent

负责根据用户输入和图片描述，生成适合 Kling AI 的图生视频 prompt。
"""

import logging
from typing import Optional
from ..services import llm

logger = logging.getLogger(__name__)


# System prompt for Kling prompt generation
SA_A_SYSTEM_PROMPT = """You are an expert prompt engineer for Kling AI's image-to-video generation model.

Your task is to create detailed, effective English prompts that generate high-quality animations from static images.

## Prompt Guidelines

1. **Subject Description**: Briefly describe the main subject
   - Character type (anime girl, realistic person, animal, etc.)
   - Key visual features that should remain consistent

2. **Action Description**: Clearly describe the main action/motion
   - Use present tense, active verbs
   - Be VERY specific about the type, direction, and timing of motion
   - Example: "The anime character takes a slow step forward with her left foot, then brings her right foot to meet it, walking at a steady pace"

3. **Motion Quality**:
   - Specify motion characteristics: smooth, natural, fluid, gentle, dynamic
   - Add temporal adverbs: slowly, gradually, continuously, rhythmically
   - Mention camera: static camera, slight zoom, etc.

4. **Visual Consistency**:
   - Emphasize maintaining original art style
   - Mention preserving colors, lighting, and character appearance

5. **Technical Constraints**:
   - Output ONLY in English
   - Prompts can be 150-300 characters for better detail
   - Focus on ONE primary action per prompt
   - Make the action description DETAILED and SPECIFIC

6. **Output Format**:
   Return ONLY the prompt text, no explanations.

## Examples

Good: "An anime character with blue hair slowly walks forward, taking gentle steps. The character's body moves naturally with each step, arms swinging slightly. The original art style and colors are preserved. Smooth, fluid motion throughout the 5-second animation."

Bad: "Character walks" (too vague)"""


# System prompt for prompt optimization when QC feedback is provided
SA_A_OPTIMIZATION_PROMPT = """You are an expert prompt engineer specializing in refining animation prompts based on quality feedback.

Your task is to optimize an existing Kling AI prompt to address specific quality issues identified during review.

## Optimization Guidelines

1. **Analyze the Feedback**: Understand what went wrong
   - Action mismatch: The motion didn't match the intended action
   - Inconsistency: Character appearance changed
   - Poor quality: Jerky motion, artifacts, unnatural movement

2. **Refinement Strategy**:
   - For action issues: Be MUCH more specific about exact body parts, direction, speed, and timing
   - For inconsistency issues: Add "maintain original appearance", "preserve character design"
   - For quality issues: Add "smooth gradual motion", "natural fluid movement", "no jerky motion"

3. **Output Requirements**:
   - Output ONLY in English
   - Make prompts 150-300 characters with detailed action descriptions
   - Focus on addressing the specific issues from feedback
   - Be VERY specific about what body parts move and how

4. **Output Format**:
   Return ONLY the optimized prompt text, no explanations.

## Example

Original: "Character walks"
Optimized: "The anime character takes slow, deliberate steps forward. Left foot moves first, then right foot follows. Body weight shifts naturally with each step. Arms swing gently at sides. Original art style and colors preserved throughout. Smooth, natural walking motion."
"""


# 专为2D横版游戏设计的追问选项（固定3个问题）
QUESTION_TEMPLATES = [
    {
        "id": "character_personality",
        "question": "请选择角色性格",
        "options": ["活泼可爱", "阳光帅气", "冷血无情", "其他（自填）"]
    },
    {
        "id": "action_type",
        "question": "请选择动作类型",
        "options": ["行走", "跑步", "跳跃", "攻击"]
    },
    {
        "id": "camera_angle",
        "question": "请选择镜头角度",
        "options": ["正面", "侧面"]
    }
]


async def check_sufficiency(image_path: str, user_description: str) -> dict:
    """
    Check if the user's input contains sufficient information for animation generation.

    简化版：直接使用固定的问题模板，不再调用 LLM。
    判断逻辑：如果 user_description 长度小于 10 个字符，认为信息不足。

    Args:
        image_path: Path to the input image (unused, kept for API compatibility)
        user_description: User's description of the desired animation

    Returns:
        dict: Contains "sufficient" (bool) and optionally "questions" (list of question objects)
    """
    logger.info("  🔹 [SA_A] 检查信息充足性...")

    if not user_description:
        raise ValueError("user_description cannot be empty")

    # 简单判断：描述太短则认为信息不足
    if len(user_description.strip()) < 10:
        logger.info("  🔹 [SA_A] 信息不足，返回选择题")
        return {
            "sufficient": False,
            "questions": QUESTION_TEMPLATES
        }

    logger.info("  🔹 [SA_A] ✅ 信息充足")
    return {"sufficient": True}


async def generate_prompt(
    user_input: str,
    image_description: str,
    qc_feedback: Optional[str] = None
) -> str:
    """
    Generate an optimized Kling AI prompt for image-to-video generation.

    Args:
        user_input: User's natural language description of desired animation
        image_description: Description of the input image content
        qc_feedback: Optional quality control feedback from previous generation attempt.
                     If provided, the prompt will be optimized to address the issues.

    Returns:
        str: Generated English prompt optimized for Kling AI image-to-video

    Raises:
        ValueError: If required parameters are empty
        RuntimeError: If LLM service call fails
    """
    logger.info("  🔹 [SA_A] 生成动画 Prompt...")

    if not user_input:
        raise ValueError("user_input cannot be empty")

    if not image_description:
        raise ValueError("image_description cannot be empty")

    # Select appropriate system prompt based on whether we have QC feedback
    system_prompt = SA_A_OPTIMIZATION_PROMPT if qc_feedback else SA_A_SYSTEM_PROMPT

    # Construct the user message
    if qc_feedback:
        user_message = f"""Original User Request: {user_input}

Input Image Description: {image_description}

Quality Control Feedback (what went wrong):
{qc_feedback}

Please generate an optimized prompt that addresses these issues."""
    else:
        user_message = f"""User Request: {user_input}

Input Image Description: {image_description}

Please generate an optimal Kling AI prompt based on the user's request and the image description."""

    try:
        result = await llm.chat(
            system_prompt=system_prompt,
            user_message=user_message
        )

        # Clean up the result - remove quotes if LLM wrapped it
        cleaned_prompt = result.strip().strip('"').strip("'")

        logger.info(f"  🔹 [SA_A] ✅ Prompt 生成成功 ({len(cleaned_prompt)} 字符):")
        logger.info(f"    📝 {cleaned_prompt}")
        return cleaned_prompt

    except Exception as e:
        logger.error(f"  🔹 [SA_A] ❌ Prompt 生成失败: {type(e).__name__}: {e}")
        raise RuntimeError(f"Prompt generation failed: {e}") from e
