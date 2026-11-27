from src.defense.countermeasures import build_countermeasure_plan


def test_ddos_plan_targets_deployment_with_immediate_controls():
    plan = build_countermeasure_plan("ddos", "deployment", "critical")

    assert plan.attack_category == "ddos"
    assert plan.affected_stage == "deployment"
    assert plan.preventive
    assert plan.immediate
    assert plan.recovery
    assert plan.validation
    assert any(item["control"] == "DDoS shielding" for item in plan.preventive)


def test_infiltration_plan_targets_supplier():
    plan = build_countermeasure_plan("infiltration", "supplier", "critical")

    assert any(item["stage"] == "supplier" for item in plan.preventive)
    assert any(item["control"] == "Suspend upstream promotion" for item in plan.immediate)
