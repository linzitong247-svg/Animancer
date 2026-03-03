"""
Agents Module - Master Agent and Sub-Agents

导出所有 Agent 的公共接口。
"""

from .sa_a import generate_prompt
from .sa_g import generate_animation
from .sa_qc import quality_check

__all__ = [
    # Sub-Agent exports
    "generate_prompt",
    "generate_animation",
    "quality_check",
]
