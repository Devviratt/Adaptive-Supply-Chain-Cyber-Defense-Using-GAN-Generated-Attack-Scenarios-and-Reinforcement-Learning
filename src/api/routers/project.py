"""
Project status router.

Provides project metadata, team info, and module status.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()

# Module status — updated as features are implemented
MODULE_STATUS = {
    "data_pipeline": {"status": "not_started", "description": "CIC-IDS2017 preprocessing"},
    "gan": {"status": "not_started", "description": "CTGAN synthetic data generation"},
    "scenario_mapper": {"status": "not_started", "description": "Attack scenario mapping"},
    "supply_chain_env": {
        "status": "not_started",
        "description": "Gymnasium supply chain environment",
    },
    "dqn": {"status": "not_started", "description": "DQN defense agent"},
    "ppo": {"status": "not_started", "description": "PPO comparison (optional)"},
    "baseline": {"status": "not_started", "description": "Rule-based baseline policy"},
    "evaluation": {"status": "not_started", "description": "Evaluation engine"},
    "backend": {"status": "in_progress", "description": "FastAPI backend"},
    "frontend": {"status": "in_progress", "description": "React dashboard"},
    "testing": {"status": "in_progress", "description": "Test suite"},
    "documentation": {"status": "in_progress", "description": "Project documentation"},
}

TEAM_MEMBERS = [
    {
        "name": "C A Anandavarthan",
        "usn": "ENG23CS0039",
        "section": "7A",
        "primary_responsibilities": [
            "Project architecture",
            "Backend integration",
            "Supply-chain environment",
            "System integration",
            "Release coordination",
        ],
    },
    {
        "name": "Deekshay G",
        "usn": "ENG23CS0055",
        "section": "7A",
        "primary_responsibilities": [
            "Data preprocessing",
            "GAN / CTGAN",
            "Synthetic data validation",
            "Data experiments",
        ],
    },
    {
        "name": "Dev Virat",
        "usn": "ENG24CS1022",
        "section": "7A",
        "primary_responsibilities": [
            "Reinforcement learning",
            "DQN agent",
            "PPO comparison (if feasible)",
            "Evaluation experiments",
        ],
    },
]


@router.get("/status")
async def project_status():
    """Get current project status and module completion."""
    completed = sum(1 for m in MODULE_STATUS.values() if m["status"] == "done")
    total = len(MODULE_STATUS)
    in_progress = sum(1 for m in MODULE_STATUS.values() if m["status"] == "in_progress")

    return {
        "project": "Adaptive Supply Chain Cyber Defense Using GAN-Generated Attack Scenarios and Reinforcement Learning",
        "team_number": 84,
        "college": "Dayananda Sagar University — School of Engineering",
        "department": "Computer Science and Engineering",
        "guide": "Prof. Namyapriya D",
        "version": "0.1.0",
        "current_phase": "Phase 1 — Foundation",
        "progress": {
            "completed_modules": completed,
            "in_progress_modules": in_progress,
            "total_modules": total,
            "percentage": round((completed / total) * 100, 1) if total > 0 else 0,
        },
        "modules": MODULE_STATUS,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/team")
async def team_info():
    """Get team member information and responsibilities."""
    return {
        "team_number": 84,
        "members": TEAM_MEMBERS,
        "shared_responsibilities": [
            "Testing",
            "Documentation",
            "Presentation preparation",
            "Bug fixing",
            "Final integration",
        ],
    }
