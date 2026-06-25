from __future__ import annotations
from dataclasses import dataclass
import math

PIPELINE_VERSION = "2.0.0"
RULES_VERSION   = "2.0.0"

# ── Feature Weights (Continuous Scoring, no strict rules) ──────────────
WEIGHT_ELIGIBILITY              = 0.15
WEIGHT_CAREER                   = 0.15
WEIGHT_SEMANTIC_MATCH           = 0.40
WEIGHT_RECRUITABILITY           = 0.15
WEIGHT_TRUST                    = 0.15

assert abs(
    WEIGHT_ELIGIBILITY + WEIGHT_CAREER + WEIGHT_SEMANTIC_MATCH +
    WEIGHT_RECRUITABILITY + WEIGHT_TRUST - 1.0
) < 1e-9, "Weights must sum to 1.0"

# ── Sigmoid Parameters ─────────────────────────────────────────────────────
# We use sigmoid to avoid threshold fragility. score = 1 / (1 + exp(-k * (x - x0)))
def sigmoid(x: float, k: float, x0: float) -> float:
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))

# ── Embeddings ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL                 = "msmarco-distilbert-base-v4"
EMBEDDING_DIM                   = 768

# ── Stage thresholds (Softened to penalties instead of eliminations) ───────
STAGE1_MIN_YEARS_EXPERIENCE     = 2.0
STAGE1_MAX_SERVICE_RATIO        = 0.85
STAGE1_DISQUALIFIED_TITLES      = ["hr", "recruiter", "accountant", "sales", "marketing", "operations"]
STAGE2_TARGET_BUILDER           = 40.0
STAGE2_TARGET_SHIPPER           = 35.0

STAGE3_TOP_K                    = 1000   # Keep mostly everyone, let ranker decide

# ── Trust Score thresholds ─────────────────────────────────────────────────
TRUST_PENALTY_TITLE_SKILL_MISMATCH  = 40
TRUST_PENALTY_SKILL_EXPLOSION       = 25
TRUST_PENALTY_CONSULTING_DISGUISE   = 20
TRUST_BOOST_GITHUB_CORROBORATION    = 20
TRUST_BOOST_CONSISTENT_ARC          = 15
TRUST_BOOST_CAREER_CHANGER_BYPASS   = 30  # genuine pivot with evidence

# ── Confidence & Uncertainty ───────────────────────────────────────────────
CONFIDENCE_BASE                 = 50.0
UNCERTAINTY_MULTIPLIER          = 0.2    # Translates (100 - confidence) to a prediction interval +/-

# ── Output ─────────────────────────────────────────────────────────────────
FINAL_TOP_N                     = 50
OUTPUT_PATH                     = "outputs/final_ranking.json"
LOG_PATH                        = "outputs/run.log"
