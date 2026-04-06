"""Shim when the rd-agent-mcp repo root is on ``sys.path``.

``from functions import run_agent_pipeline, research_phase``
"""

from rd_agent_mcp.functions import (
    latex_section_critique_build_prompt,
    latex_section_critique_get_bundle,
    latex_section_critique_index_ground_truth,
    latex_section_critique_merge_partial,
    latex_section_critique_retrieve_ground_truth,
    latex_section_critique_run_cross_cutting,
    latex_section_critique_run_section_review,
    research_phase,
    research_phase_async,
    run_agent_pipeline,
    run_agent_pipeline_async,
)

__all__ = [
    "latex_section_critique_build_prompt",
    "latex_section_critique_get_bundle",
    "latex_section_critique_index_ground_truth",
    "latex_section_critique_merge_partial",
    "latex_section_critique_retrieve_ground_truth",
    "latex_section_critique_run_cross_cutting",
    "latex_section_critique_run_section_review",
    "research_phase",
    "research_phase_async",
    "run_agent_pipeline",
    "run_agent_pipeline_async",
]
