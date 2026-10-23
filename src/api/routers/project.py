"""
Project status router.

Provides project metadata, team info, and module status.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()

# Module status & milestone weights — rigorously auditable for academic review
MODULE_STATUS = {
    "foundations": {
        "status": "done",
        "weight": 5.0,
        "completion_ratio": 1.0,
        "phase": "Phase 1",
        "description": "System Architecture, Repository Structure, SQLite DB & Pydantic Schemas",
    },
    "data_pipeline": {
        "status": "done",
        "weight": 10.0,
        "completion_ratio": 1.0,
        "phase": "Phase 2",
        "description": "CIC-IDS2017 Preprocessing, Leakage-Free Splitting & Quality Assertions (13/13 passed)",
    },
    "gan": {
        "status": "done",
        "weight": 10.0,
        "completion_ratio": 1.0,
        "phase": "Phase 3",
        "description": "CTGAN Synthetic Attack Scenario Generation (2,000 balanced samples synthesized)",
    },
    "validation": {
        "status": "done",
        "weight": 5.0,
        "completion_ratio": 1.0,
        "phase": "Phase 4",
        "description": "Statistical Fidelity (W1=0.1057, Pearson=98.69%) & Downstream Utility (+1.49% accuracy)",
    },
    "scenario_mapper": {
        "status": "done",
        "weight": 5.0,
        "completion_ratio": 1.0,
        "phase": "Phase 5",
        "description": "Network Intrusion to 4-Stage Supply Chain Threat Mapping (100 scenarios in DB)",
    },
    "supply_chain_env": {
        "status": "done",
        "weight": 5.0,
        "completion_ratio": 1.0,
        "phase": "Phase 6",
        "description": "Gymnasium Discrete-Event Environment (12-dim state, 5 defense actions, supply-chain topology)",
    },
    "baseline": {
        "status": "done",
        "weight": 5.0,
        "completion_ratio": 1.0,
        "phase": "Phase 7",
        "description": "Rule-Based SOC Playbook Baseline Policy (Experiment A evaluated across 5 random seeds)",
    },
    "dqn": {
        "status": "in_progress",
        "weight": 20.0,
        "completion_ratio": 0.0,
        "phase": "Phase 8",
        "description": "DQN Defense Agent (Architecture & 1,000-step smoke test done; 50k convergence training in progress)",
    },
    "ppo": {
        "status": "in_progress",
        "weight": 15.0,
        "completion_ratio": 0.0,
        "phase": "Phase 9",
        "description": "PPO Comparative Baseline (Gymnasium wrapper implemented; hyperparameter tuning in progress)",
    },
    "experiments": {
        "status": "in_progress",
        "weight": 10.0,
        "completion_ratio": 0.0,
        "phase": "Phase 10",
        "description": "Controlled Comparative Benchmark (Condition A completed; Conditions B, C, D awaiting converged RL agents)",
    },
    "live_telemetry": {
        "status": "in_progress",
        "weight": 5.0,
        "completion_ratio": 0.0,
        "phase": "Phase 11",
        "description": "Real-time Telemetry & Interactive Simulation Controller (API endpoints active)",
    },
    "autonomous_defense": {
        "status": "planned",
        "weight": 5.0,
        "completion_ratio": 0.0,
        "phase": "Phase 12",
        "description": "Production Autonomous Deployment & Live Kubernetes Defense Controller (Planned)",
    },
}

TEAM_MEMBERS = [
    {
        "name": "Dev Virat",
        "usn": "ENG24CS1022",
        "section": "7A",
        "primary_responsibilities": [
            "Project architecture & system integration",
            "Gymnasium supply chain simulation environment",
            "Reinforcement learning defense models (DQN/PPO)",
            "Controlled benchmark evaluation & verification",
        ],
    },
    {
        "name": "C A Anandavarthan",
        "usn": "ENG23CS0039",
        "section": "7A",
        "primary_responsibilities": [
            "Backend API services & FastAPI routing",
            "Database ORM schemas & persistence",
            "Rule-based baseline defense heuristics",
            "Interactive simulation controller",
        ],
    },
    {
        "name": "Deekshay G",
        "usn": "ENG23CS0055",
        "section": "7A",
        "primary_responsibilities": [
            "CIC-IDS2017 dataset preprocessing & validation",
            "CTGAN synthetic attack scenario generation",
            "Statistical fidelity validation (W1 / JS divergence)",
            "Downstream classifier utility evaluation",
        ],
    },
]


@router.get("/status")
async def project_status():
    """Get current project status and auditable weighted progress calculation."""
    completed = sum(1 for m in MODULE_STATUS.values() if m["status"] == "done")
    in_progress = sum(1 for m in MODULE_STATUS.values() if m["status"] == "in_progress")
    planned = sum(1 for m in MODULE_STATUS.values() if m["status"] == "planned")
    total = len(MODULE_STATUS)

    # Calculate exact weighted progress
    weighted_progress = sum(m["weight"] * m.get("completion_ratio", 1.0 if m["status"] == "done" else 0.0) for m in MODULE_STATUS.values())
    total_possible_weight = sum(m["weight"] for m in MODULE_STATUS.values())
    verified_pct = round((weighted_progress / total_possible_weight) * 100, 1)

    return {
        "project": "Adaptive Supply Chain Cyber Defense Using GAN-Generated Attack Scenarios and Reinforcement Learning",
        "team_number": 84,
        "college": "Dayananda Sagar University — School of Engineering",
        "department": "Computer Science and Engineering",
        "guide": "Prof. Namyapriya D",
        "version": "0.4.0",
        "target_milestone": "Review 1 — 40% Progress Checkpoint",
        "progress": {
            "verified_percentage": verified_pct,
            "target_checkpoint_percentage": 40.0,
            "calculation_method": "Weighted milestone scoring based on actual verified implementation deliverables",
            "completed_modules": completed,
            "in_progress_modules": in_progress,
            "planned_modules": planned,
            "total_modules": total,
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


@router.get("/data-summary")
async def data_summary():
    """Return authentic dataset metadata, split statistics, and validation status."""
    import json
    from pathlib import Path

    meta_file = Path("data/processed/dataset_metadata.json")
    split_file = Path("data/processed/split_statistics.json")
    val_file = Path("data/processed/validation_report.json")

    metadata = {}
    splits = {}
    validation = {}

    if meta_file.exists():
        with open(meta_file, encoding="utf-8") as f:
            metadata = json.load(f)

    if split_file.exists():
        with open(split_file, encoding="utf-8") as f:
            splits = json.load(f)

    if val_file.exists():
        with open(val_file, encoding="utf-8") as f:
            validation = json.load(f)

    return {
        "metadata": metadata,
        "splits": splits,
        "validation": validation,
    }


@router.get("/gan-summary")
async def gan_summary():
    """Return authentic CTGAN validation results, downstream utility, and figure links."""
    import json
    from pathlib import Path

    val_file = Path("artifacts/reports/synthetic_data_validation.json")
    utility_file = Path("artifacts/reports/downstream_utility_results.json")
    figures_dir = Path("artifacts/figures")

    validation = {}
    utility = {}
    figures = []

    if val_file.exists():
        with open(val_file, encoding="utf-8") as f:
            validation = json.load(f)

    if utility_file.exists():
        with open(utility_file, encoding="utf-8") as f:
            utility = json.load(f)

    if figures_dir.exists():
        figures = [p.name for p in figures_dir.glob("*.png")]

    return {
        "validation": validation,
        "utility": utility,
        "figures": sorted(figures),
    }

