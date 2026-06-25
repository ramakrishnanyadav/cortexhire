from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypedDict, Optional

# ── Raw input ──────────────────────────────────────────────────────────────
@dataclass
class RawCandidate:
    candidate_id: str
    name: str
    title: str
    years_experience: float
    skills: list[str]           # raw skill strings
    roles: list[RawRole]
    github_score: Optional[float]
    response_rate: Optional[float]  # 0.0–1.0
    notice_period_days: Optional[int]
    open_to_work: bool
    assessment_score: Optional[float]

@dataclass
class RawRole:
    company: str
    title: str
    tenure_months: int
    is_product_company: Optional[bool] = False
    is_service_company: Optional[bool] = False
    responsibilities: list[str] = field(default_factory=list)

# ── Feature vectors ────────────────────────────────────────────────────────
@dataclass
class CareerVector:
    builder: float = 0.0        # 0–100 — shipped real products
    shipper: float = 0.0        # 0–100 — deployed to production
    researcher: float = 0.0     # 0–100 — papers / experiments only
    consultant: float = 0.0     # 0–100 — advisory, no ownership
    manager: float = 0.0        # 0–100 — people / program management
    leader: float = 0.0         # 0–100 — tech leadership with IC depth

@dataclass
class ScoredCandidate:
    raw: RawCandidate
    career_vector: Optional[CareerVector] = None
    semantic_similarity: float = 0.0
    eligibility_score: float = 0.0
    recruitability_score: float = 0.0
    trust_score: float = 0.0
    confidence_score: float = 0.0 # Uncertainty modeling
    composite_score: float = 0.0
    prediction_interval: float = 0.0 # +/- variance based on confidence
    stage_eliminated: Optional[int] = None  # None = survived all stages
    evidence: list[str] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    trust_flags: list[TrustFlag] = field(default_factory=list)

# ── Explainability ─────────────────────────────────────────────────────────

@dataclass
class TrustFlag:
    flag_type: str              # "title_skill_mismatch" | "skill_explosion" | etc.
    description: str
    penalty: float              # points deducted from trust score
    evidence: str               # specific text that triggered the flag

# ── Pipeline result ────────────────────────────────────────────────────────
@dataclass
class PipelineResult:
    top_candidates: list[ScoredCandidate]   # sorted descending by composite_score
    total_input: int
    stage_counts: dict[str, int]            # survivors after each stage
    metrics: dict[str, float]              # Precision@K, trap_rejection_rate, etc.
    run_metadata: dict[str, str]           # timestamp, version, config hash
