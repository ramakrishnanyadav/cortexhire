# stages/stage1_eligibility.py
from __future__ import annotations
from stages.base import PipelineStage
from schemas import ScoredCandidate, TrustFlag
import config

class EligibilityStage(PipelineStage):
    STAGE_NUMBER = 1
    STAGE_NAME   = "Eligibility Intelligence"

    def process(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        """
        Assigns continuous eligibility score instead of hard eliminations.
        Score is reduced if years of experience are low or service ratio is high.
        """
        for c in candidates:
            score = 100.0
            raw = c.raw

            # 1. Years of experience (Sigmoid decay if under threshold)
            # If 2.0 is the target, then 2.0 -> score ~90, 1.0 -> score ~30
            yoe_factor = config.sigmoid(raw.years_experience, k=3.0, x0=config.STAGE1_MIN_YEARS_EXPERIENCE - 0.5)
            score = score * yoe_factor

            # 2. Service ratio penalty
            service_ratio = self._service_ratio(raw)
            if service_ratio > 0.0:
                # the closer to 1.0 the ratio, the higher the penalty
                penalty_factor = config.sigmoid(service_ratio, k=-10.0, x0=config.STAGE1_MAX_SERVICE_RATIO)
                score = score * penalty_factor

            # 3. Non-technical title penalty
            normalised_title = raw.title.lower().strip()
            if any(t in normalised_title for t in config.STAGE1_DISQUALIFIED_TITLES):
                score -= 40.0
                c.trust_flags.append(TrustFlag(
                    flag_type="non_technical_title",
                    description=f"Non-technical title: '{raw.title}'",
                    penalty=0.0, # Handled by eligibility score now
                    evidence=f"title={raw.title}",
                ))

            c.eligibility_score = max(0.0, min(100.0, score))
            
            # Sparse data handling
            if raw.years_experience <= 0.0 and not raw.roles:
                 c.confidence_score -= 20.0 # Low confidence due to sparse profile

        return candidates

    def _service_ratio(self, raw) -> float:
        """
        Fraction of total tenure spent at service/consulting companies.
        """
        if not raw.roles:
            return 0.0
        total = sum(r.tenure_months for r in raw.roles)
        if total == 0:
            return 0.0
        service_tenure = sum(r.tenure_months for r in raw.roles if r.is_service_company)
        return service_tenure / total
