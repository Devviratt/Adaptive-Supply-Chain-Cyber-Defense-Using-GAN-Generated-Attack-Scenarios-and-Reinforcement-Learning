"""Attack-specific defensive controls for the supply-chain simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Countermeasure:
    control: str
    action: str
    stage: str
    priority: str
    rationale: str


@dataclass(frozen=True)
class CountermeasurePlan:
    attack_category: str
    affected_stage: str
    severity: str
    preventive: list[dict] = field(default_factory=list)
    immediate: list[dict] = field(default_factory=list)
    recovery: list[dict] = field(default_factory=list)
    validation: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


COMMON_PREVENTIVE = [
    Countermeasure("Signed dependencies", "Require signed artifacts and verify signatures in CI and at deployment.", "supplier", "critical", "Prevents unsigned or substituted upstream code from entering the pipeline."),
    Countermeasure("Dependency allowlist", "Pin dependencies and generate/verify an immutable software bill of materials.", "build", "high", "Limits unapproved packages and makes dependency drift attributable."),
    Countermeasure("Least-privilege CI", "Use ephemeral, workload-identity-based build runners with no persistent credentials.", "build", "critical", "Contains credential and build-agent compromise."),
    Countermeasure("Registry access control", "Require MFA, provenance attestations, and immutable signed release promotion.", "registry", "critical", "Prevents unauthorized package publication."),
    Countermeasure("Deployment safeguards", "Use policy-as-code, verified images, runtime allowlisting, and staged rollouts.", "deployment", "high", "Stops untrusted artifacts from reaching production."),
]

CATEGORY_CONTROLS: dict[str, list[Countermeasure]] = {
    "ddos": [
        Countermeasure("DDoS shielding", "Enable upstream L3/L4 filtering, autoscaling limits, SYN cookies, and geographic/rate-based controls.", "deployment", "critical", "Absorbs volumetric traffic before it reaches application capacity."),
        Countermeasure("Circuit breakers", "Add bulkheads and circuit breakers around public endpoints and downstream dependencies.", "deployment", "high", "Prevents overload from cascading into the full supply chain."),
    ],
    "dos": [
        Countermeasure("Traffic limiting", "Apply per-source and per-service rate limits, connection limits, and WAF throttling.", "deployment", "critical", "Reduces abuse of public endpoints."),
    ],
    "botnet": [
        Countermeasure("Build isolation", "Recreate build runners as ephemeral machines and deny lateral network access.", "build", "critical", "Prevents a bot-controlled build node from reaching peers."),
        Countermeasure("Egress filtering", "Allow build jobs only approved dependency and registry destinations.", "build", "critical", "Stops command-and-control and data exfiltration."),
    ],
    "brute_force": [
        Countermeasure("Identity hardening", "Enforce MFA, passwordless access, lockout, and impossible-travel alerts.", "build", "critical", "Reduces credential compromise risk."),
    ],
    "web_attack": [
        Countermeasure("Repository web controls", "Patch exposed services, enable WAF rules, and restrict repository administration paths.", "supplier", "critical", "Blocks exploit traffic targeting source systems."),
    ],
    "portscan": [
        Countermeasure("Attack surface reduction", "Remove unused ports, restrict management planes, and alert on reconnaissance.", "deployment", "high", "Limits discoverable services and detects probing early."),
    ],
    "infiltration": [
        Countermeasure("Developer workstation controls", "Require endpoint detection, application allowlisting, phishing-resistant MFA, and secret quarantine.", "supplier", "critical", "Contains upstream developer-account or workstation compromise."),
    ],
}

STAGE_IMMEDIATE = {
    "supplier": [
        Countermeasure("Suspend upstream promotion", "Pause source and dependency promotion until repository integrity is verified.", "supplier", "critical", "Stops malicious source changes from progressing."),
    ],
    "build": [
        Countermeasure("Quarantine build agents", "Isolate suspicious runners and revoke their credentials and signing access.", "build", "critical", "Stops malicious build output and lateral movement."),
    ],
    "registry": [
        Countermeasure("Freeze package registry", "Block new promotions and revoke compromised package publication tokens.", "registry", "critical", "Prevents distribution of a malicious artifact."),
    ],
    "deployment": [
        Countermeasure("Contain production workload", "Isolate the affected workload and route traffic to known-good capacity.", "deployment", "critical", "Preserves service while containing compromise."),
    ],
}


def build_countermeasure_plan(
    attack_category: str,
    affected_stage: str,
    severity: str,
) -> CountermeasurePlan:
    category = (attack_category or "benign").strip().lower()
    stage = (affected_stage or "deployment").strip().lower()

    preventive = [*COMMON_PREVENTIVE]
    preventive.extend(CATEGORY_CONTROLS.get(category, []))
    immediate = list(STAGE_IMMEDIATE.get(stage, STAGE_IMMEDIATE["deployment"]))
    if category not in ("benign", "portscan"):
        immediate.append(Countermeasure("Preserve evidence", "Capture logs, artifact hashes, identities, network flows, and runner snapshots.", stage, "high", "Supports attribution and repeatable incident response."))

    recovery = [
        Countermeasure("Rebuild from trust", "Replace the affected stage from reviewed, signed, and reproducible known-good artifacts.", stage, "critical", "Restores integrity instead of attempting to clean a potentially compromised system."),
        Countermeasure("Rotate credentials", "Rotate all secrets, signing keys, registry tokens, CI credentials, and deployment identities.", stage, "critical", "Invalidates access established by the attacker."),
    ]
    validation = [
        Countermeasure("Integrity verification", "Verify hashes, signatures, provenance attestations, SBOMs, and configuration drift.", stage, "critical", "Confirms the rebuilt environment matches an approved baseline."),
        Countermeasure("Monitored rollout", "Restore one segment at a time and watch availability, identity, egress, and integrity telemetry.", stage, "high", "Detects reinfection or residual attack activity before full recovery."),
    ]

    return CountermeasurePlan(
        attack_category=category,
        affected_stage=stage,
        severity=(severity or "medium").strip().lower(),
        preventive=[asdict(item) for item in preventive],
        immediate=[asdict(item) for item in immediate],
        recovery=[asdict(item) for item in recovery],
        validation=[asdict(item) for item in validation],
    )
