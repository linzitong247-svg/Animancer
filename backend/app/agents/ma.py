"""
Master Agent (MA) - Main Orchestration Agent

负责协调所有子 Agent（SA_A, SA_G, SA_QC），管理会话状态，实现完整的动画生成流程。

功能：
- 管理会话状态（图片、prompt、历史记录）
- 信息充足性检查
- 子 Agent 编排调度
- 质检失败时的重试逻辑
- 用户追问处理
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .sa_a import generate_prompt, check_sufficiency
from .sa_g import generate_animation
from .sa_qc import quality_check

logger = logging.getLogger(__name__)


def _log_pipeline_step(step: str, status: str, details: str = ""):
    """
    统一的流程日志输出格式

    Args:
        step: 步骤名称
        status: 状态 (START|END|ERROR|INFO)
        details: 详细信息
    """
    border = "=" * 60
    if status == "START":
        logger.info(f"\n{border}\n▶▶▶ [{step}] 开始\n{border}")
    elif status == "END":
        logger.info(f"{border}\n◀◀◀ [{step}] 完成\n{details}\n{border}")
    elif status == "ERROR":
        logger.error(f"{border}\n✖✖✖ [{step}] 失败\n{details}\n{border}")
    else:
        logger.info(f"  └─ [{step}] {details}")


def _log_data_flow(node: str, input_data: str, output_data: str = ""):
    """
    数据流日志 - 显示节点间的数据传递

    Args:
        node: 节点名称
        input_data: 输入数据摘要
        output_data: 输出数据摘要
    """
    logger.info(f"  📊 [{node}]")
    logger.info(f"     输入: {input_data}")
    if output_data:
        logger.info(f"     输出: {output_data}")

# 会话存储：key 为 session_id，value 为会话状态字典
sessions: Dict[str, Dict[str, Any]] = {}

# 最大重试次数
MAX_RETRY_COUNT = 3

# 信息充足性检查的系统提示
SUFFICIENCY_CHECK_SYSTEM_PROMPT = """你是一个动画需求分析专家。你需要判断用户提供的信息是否足以生成一个高质量的动画。

判断标准：
1. 是否有明确的动作描述（如"人物挥手"、"跑动"、"跳舞"等）
2. 是否有运动方向或轨迹的描述（可选，但有助于提升质量）
3. 是否有动画风格或效果的偏好（可选）

如果信息充足，返回：{"sufficient": true}
如果信息不足，返回：{"sufficient": false, "questions": ["问题1", "问题2", ...]}

请以 JSON 格式输出，不要包含任何其他内容。"""


async def start_generation(
    session_id: str,
    image_path: str,
    prompt: str
) -> Dict[str, Any]:
    """
    开始动画生成流程

    首先检查用户输入的信息是否充足，如果充足则依次调度 SA_A -> SA_G -> SA_QC。
    如果信息不足，返回需要追问的问题列表。

    Args:
        session_id: 会话唯一标识符
        image_path: 输入图片的路径
        prompt: 用户的动画描述

    Returns:
        dict: 包含状态和相应数据的字典：
            - 如果信息不足: {"status": "need_more_info", "questions": [...]}
            - 如果生成中: {"status": "processing", "message": "..."}
            - 如果完成: {"status": "completed", "video_path": "...", "qc_result": {...}}

    Raises:
        ValueError: 如果参数无效
        RuntimeError: 如果生成过程失败
    """
    _log_pipeline_step("ANIMATION PIPELINE", "START", f"session_id={session_id}")

    if not session_id:
        raise ValueError("session_id 不能为空")

    if not image_path:
        raise ValueError("image_path 不能为空")

    if not prompt:
        raise ValueError("prompt 不能为空")

    # 验证图片文件存在
    image_file = Path(image_path)
    if not image_file.exists():
        _log_pipeline_step("INPUT VALIDATION", "ERROR", f"图片文件不存在: {image_path}")
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    _log_data_flow("INPUT",
        f"session_id={session_id}, image={image_file.name} ({image_file.stat().st_size} bytes)",
        f"prompt={prompt[:80]}...")

    # 初始化会话状态
    sessions[session_id] = {
        "image_path": image_path,
        "user_prompt": prompt,
        "history": [],
        "state": "started",
        "retry_count": 0,
        "generated_prompts": [],
        "qc_reports": [],
        "start_time": time.time()
    }
    _log_pipeline_step("SESSION", "INFO", f"会话已初始化")

    # Step 1: 检查信息是否充足
    _log_pipeline_step("STEP 1: SUFFICIENCY CHECK", "START")
    try:
        sufficiency_result = await check_sufficiency(
            image_path=image_path,
            user_description=prompt
        )

        is_sufficient = sufficiency_result.get("sufficient", True)
        _log_pipeline_step("STEP 1: SUFFICIENCY CHECK", "END",
            f"sufficient={is_sufficient}")

        if not is_sufficient:
            logger.info("  ⏸️ 流程暂停: 等待用户补充信息")
            sessions[session_id]["state"] = "awaiting_info"
            return {
                "status": "need_more_info",
                "questions": sufficiency_result.get("questions", [
                    "请提供更详细的动作描述，例如您希望角色做什么动作？"
                ])
            }
    except Exception as e:
        _log_pipeline_step("STEP 1: SUFFICIENCY CHECK", "ERROR",
            f"异常: {type(e).__name__}: {e}，继续流程")
        logger.warning("[MA] 继续流程（跳过充足性检查）")

    # 信息充足，开始生成流程
    return await _execute_generation_pipeline(session_id)


async def continue_generation(
    session_id: str,
    answer: str
) -> Dict[str, Any]:
    """
    继续动画生成流程（接收追问回答后）

    Args:
        session_id: 会话唯一标识符
        answer: 用户对追问的回答

    Returns:
        dict: 包含状态和相应数据的字典

    Raises:
        ValueError: 如果 session_id 无效或参数无效
        RuntimeError: 如果生成过程失败
    """
    if not session_id:
        raise ValueError("session_id 不能为空")

    if not answer:
        raise ValueError("answer 不能为空")

    # 检查会话是否存在
    if session_id not in sessions:
        raise ValueError(f"无效的 session_id: {session_id}")

    session = sessions[session_id]
    logger.info(f"MA: 继续生成流程 - session={session_id}")

    # 更新会话状态
    session["user_prompt"] += f"\n\n用户补充: {answer}"
    session["history"].append({"role": "user", "content": answer})
    session["state"] = "generating"

    # 执行生成流程
    return await _execute_generation_pipeline(session_id)


async def _execute_generation_pipeline(
    session_id: str
) -> Dict[str, Any]:
    """
    执行完整的生成流程：SA_A -> SA_G -> SA_QC（带重试）

    Args:
        session_id: 会话唯一标识符

    Returns:
        dict: 生成结果
    """
    session = sessions[session_id]
    retry_count = session.get("retry_count", 0)
    start_time = time.time()

    if retry_count > 0:
        logger.info(f"\n{'🔄' * 20}\n  重试 #{retry_count}/{MAX_RETRY_COUNT}\n{'🔄' * 20}")

    # ========== STEP 2: SA_A - Prompt Generation ==========
    _log_pipeline_step("STEP 2: SA_A (Prompt Generation)", "START")

    # 获取上一次的质检报告（如果有）
    qc_feedback = None
    if retry_count > 0 and session.get("qc_reports"):
        latest_qc = session["qc_reports"][-1]
        qc_feedback = latest_qc.get("report", "")
        if "overall_score" in latest_qc:
            qc_feedback += f" (评分: {latest_qc['overall_score']}/100)"
        action_score = latest_qc.get("action_score", "N/A")
        consistency_score = latest_qc.get("consistency_score", "N/A")
        motion_score = latest_qc.get("motion_score", "N/A")
        qc_feedback += f" [动作: {action_score}, 一致性: {consistency_score}, 质量: {motion_score}]"
        _log_pipeline_step("SA_A", "INFO", f"使用 QC 反馈优化: {qc_feedback[:80]}...")

    try:
        generated_prompt = await generate_prompt(
            user_input=session["user_prompt"],
            image_description=f"图片路径: {session['image_path']}",
            qc_feedback=qc_feedback
        )

        session["generated_prompts"].append(generated_prompt)
        _log_data_flow("SA_A → SA_G",
            f"user_prompt={session['user_prompt'][:50]}...",
            f"generated_prompt={generated_prompt[:80]}...")
        _log_pipeline_step("STEP 2: SA_A (Prompt Generation)", "END",
            f"prompt 长度={len(generated_prompt)}")

    except Exception as e:
        _log_pipeline_step("STEP 2: SA_A (Prompt Generation)", "ERROR", str(e))
        session["state"] = "error"
        return {"status": "error", "session_id": session_id, "error": str(e)}

    # ========== STEP 3: SA_G - Animation Generation ==========
    _log_pipeline_step("STEP 3: SA_G (Animation Generation)", "START")
    step_start = time.time()

    try:
        video_path = await generate_animation(
            image_path=session["image_path"],
            prompt=generated_prompt
        )

        video_file = Path(video_path)
        video_size = video_file.stat().st_size if video_file.exists() else 0
        step_duration = time.time() - step_start

        _log_data_flow("SA_G → SA_QC",
            f"prompt={generated_prompt[:50]}...",
            f"video={video_file.name} ({video_size} bytes)")
        _log_pipeline_step("STEP 3: SA_G (Animation Generation)", "END",
            f"video_path={video_path}, 耗时={step_duration:.1f}s")

    except Exception as e:
        _log_pipeline_step("STEP 3: SA_G (Animation Generation)", "ERROR", str(e))
        session["state"] = "error"
        return {"status": "error", "session_id": session_id, "error": str(e)}

    # ========== STEP 4: SA_QC - Quality Control ==========
    _log_pipeline_step("STEP 4: SA_QC (Quality Control)", "START")
    step_start = time.time()

    try:
        qc_result = await quality_check(
            video_path=video_path,
            original_prompt=session["user_prompt"]
        )

        session["qc_reports"].append(qc_result)
        step_duration = time.time() - step_start

        passed = qc_result.get("passed", False)
        overall_score = qc_result.get("overall_score", "N/A")
        action_score = qc_result.get("action_score", "N/A")
        consistency_score = qc_result.get("consistency_score", "N/A")
        motion_score = qc_result.get("motion_score", "N/A")

        status_icon = "✅" if passed else "❌"
        _log_pipeline_step("STEP 4: SA_QC (Quality Control)", "END" if passed else "INFO",
            f"{status_icon} passed={passed}, overall={overall_score}, "
            f"action={action_score}, consistency={consistency_score}, motion={motion_score}, "
            f"耗时={step_duration:.1f}s")

    except Exception as e:
        _log_pipeline_step("STEP 4: SA_QC (Quality Control)", "ERROR", str(e))
        session["state"] = "error"
        return {"status": "error", "session_id": session_id, "error": str(e)}

    # ========== 检查结果 ==========
    if qc_result["passed"]:
        # 质检通过，返回结果
        session["state"] = "completed"
        session["video_path"] = video_path
        total_duration = time.time() - start_time

        # 生成可访问的视频 URL
        video_filename = Path(video_path).name
        video_url = f"/videos/{video_filename}"

        logger.info(f"\n{'🎉' * 20}")
        logger.info(f"  动画生成成功!")
        logger.info(f"  总耗时: {total_duration:.1f}s")
        logger.info(f"  重试次数: {retry_count}")
        logger.info(f"  视频路径: {video_path}")
        logger.info(f"  视频URL: {video_url}")
        logger.info(f"{'🎉' * 20}\n")

        return {
            "status": "completed",
            "session_id": session_id,
            "video_path": video_path,
            "video_url": video_url,
            "qc_result": qc_result,
            "generated_prompt": generated_prompt,
            "retry_count": retry_count
        }
    else:
        # 质检未通过，检查是否可以重试
        if retry_count < MAX_RETRY_COUNT:
            logger.info(f"  ⚠️ 质检未通过，准备重试 ({retry_count + 1}/{MAX_RETRY_COUNT})")
            session["retry_count"] = retry_count + 1
            session["state"] = "retrying"

            await asyncio.sleep(0.5)
            return await _execute_generation_pipeline(session_id)
        else:
            # 达到最大重试次数，返回失败结果
            logger.warning(f"\n{'❌' * 20}\n  达到最大重试次数\n{'❌' * 20}\n")
            session["state"] = "failed"
            return {
                "status": "failed",
                "session_id": session_id,
                "video_path": video_path,
                "qc_result": qc_result,
                "generated_prompt": generated_prompt,
                "error": "达到最大重试次数，质检仍未通过"
            }


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    获取会话状态

    Args:
        session_id: 会话唯一标识符

    Returns:
        dict: 会话状态字典，如果不存在返回 None
    """
    return sessions.get(session_id)


def clear_session(session_id: str) -> bool:
    """
    清除会话状态

    Args:
        session_id: 会话唯一标识符

    Returns:
        bool: 是否成功清除
    """
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"MA: 清除会话 - session={session_id}")
        return True
    return False


def get_all_sessions() -> Dict[str, Dict[str, Any]]:
    """
    获取所有会话状态（用于调试）

    Returns:
        dict: 所有会话的副本
    """
    return {sid: session.copy() for sid, session in sessions.items()}
