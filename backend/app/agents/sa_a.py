"""
Sub-Agent A (SA_A) - Animation Prompt Generation Agent

负责根据用户输入和图片描述，生成适合 Kling AI 的图生视频 prompt。
"""

import logging
from typing import Optional
from ..services import llm

logger = logging.getLogger(__name__)


# System prompt for Kling prompt generation
SA_A_SYSTEM_PROMPT = """You are an expert prompt engineer for Kling AI's image-to-video generation model, specializing in **2D side-scrolling game character animations**.

Your task is to create detailed, effective English prompts that generate high-quality 2D game-style sprite animations from static character images.

## 2D Game Animation Context

The output will be used as sprite animation for a 2D side-scrolling game. Keep these constraints in mind at ALL times:
- **Side-view framing**: The character is viewed from the side (or front if user specifies). NO 3D perspective changes, NO camera rotation.
- **Static camera**: The camera is completely fixed. Only the character moves.
- **Loop-friendly motion**: The animation should start and end in a similar pose so it can loop seamlessly in a game engine.
- **Clean silhouette**: The character's outline should remain clear and readable against any background.
- **Exaggerated, readable poses**: Game animations need distinct key poses that read clearly at small sizes. Favor stylized, snappy movement over realistic physics.
- **Consistent scale**: The character should not grow, shrink, or shift position on screen.
- **Minimal background**: Focus entirely on the character's body movement. No background elements should move or change.
- **Stay within frame**: The character must remain fully visible within the frame at all times. No body parts should be cut off or extend beyond the edges of the frame.

## Prompt Guidelines

1. **Subject Description**: Briefly describe the main subject
   - Character type (anime character, pixel art warrior, fantasy hero, etc.)
   - Key visual features that should remain consistent

2. **Action Description**: Clearly describe the game action
   - Use present tense, active verbs
   - Be VERY specific about body part movement, direction, and timing
   - Frame the action as a game animation cycle (idle, walk, run, attack, jump, etc.)
   - Example: "The 2D anime character performs a side-view walk cycle, stepping forward with exaggerated leg movement. Arms swing naturally at sides. The pose returns to starting position for seamless looping."

3. **Motion Quality**:
   - Specify: smooth, stylized, snappy, fluid, rhythmic
   - Emphasize loop-friendly timing
   - Always include: "static camera, side view, no background movement"

4. **Visual Consistency**:
   - Emphasize maintaining original 2D art style
   - Mention preserving colors, proportions, and character design
   - Stress: "character remains at consistent scale and position"

5. **Technical Constraints**:
   - Output ONLY in English
   - Prompts should be 150-300 characters for detail
   - Focus on ONE game animation action per prompt
   - Always mention side-view and static camera
   - Emphasize the animation should return to starting pose for looping

6. **Output Format**:
   Return ONLY the prompt text, no explanations.

## Examples

Good: "2D side-view anime character performs a walk cycle. Left foot steps forward, then right foot follows in rhythmic pattern. Arms swing gently at sides. Character maintains consistent scale and position. Static camera, no background movement. Stylized, exaggerated steps suitable for game sprite animation. Pose returns to start for seamless loop."

Bad: "Character walks" (too vague, no game context)
Bad: "Camera rotates around the walking character" (3D camera movement, not suitable for 2D game)"""


# System prompt for prompt optimization when QC feedback is provided
SA_A_OPTIMIZATION_PROMPT = """You are an expert prompt engineer specializing in refining 2D game animation prompts based on quality feedback.

Your task is to optimize an existing Kling AI prompt to address specific quality issues identified during review, while maintaining 2D side-scrolling game animation standards.

## Optimization Guidelines

1. **Analyze the Feedback**: Understand what went wrong
   - Action mismatch: The motion didn't match the intended game action
   - Inconsistency: Character appearance, scale, or proportions changed between frames
   - Poor quality: Artifacts, deformation, blurry frames, limb distortion
   - Loop issue: Animation doesn't return to starting pose

2. **Refinement Strategy**:
   - For action issues: Be MUCH more specific about exact body parts, direction, speed, and timing. Frame it as a game animation cycle.
   - For inconsistency issues: Add "maintain original 2D art style", "preserve character design and scale", "consistent proportions throughout"
   - For quality issues: Add "clean character silhouette", "no deformation or artifacts", "sharp readable poses"
   - For loop issues: Add "animation returns to starting pose for seamless looping"
   - ALWAYS ensure: "static camera, side view, no background movement, consistent character position and scale"

3. **Output Requirements**:
   - Output ONLY in English
   - Make prompts 150-300 characters with detailed action descriptions
   - Focus on addressing the specific issues from feedback
   - Maintain 2D game sprite animation context

4. **Output Format**:
   Return ONLY the optimized prompt text, no explanations.

## Example

Original: "Character walks"
Optimized: "2D side-view anime character performs a walk cycle. Left foot steps forward with exaggerated motion, then right foot follows. Body weight shifts with each step, arms swing at sides. Character stays at consistent scale and position. Static camera, no background movement. Pose returns to start for seamless game loop."
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
