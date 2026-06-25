# stages/stage4_recruitability.py
from __future__ import annotations
from stages.base import PipelineStage
from schemas import ScoredCandidate
import config

class RecruitabilityStage(PipelineStage):
    STAGE_NUMBER = 4
    STAGE_NAME   = "Behavioural Availability Scorer"

    def process(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        """
        Continuous scoring for behavioral features. Does not eliminate.
        """
        for c in candidates:
            c.recruitability_score = self._score_candidate(c)

        return candidates

    def _score_candidate(self, c: ScoredCandidate) -> float:
        score = 50.0  # Baseline
        
        # 1. Response Rate
        if c.raw.response_rate is not None:
            # Continuous mapping instead of hard threshold
            response_bonus = (c.raw.response_rate - 0.5) * 50.0
            score += response_bonus
        else:
            c.confidence_score -= 5.0 # Missing behavioral data reduces confidence slightly
                
        # 2. Open to Work
        if c.raw.open_to_work:
            score += 15.0
        else:
            score -= 10.0
            
        # 3. Notice Period (Continuous penalty)
        if c.raw.notice_period_days is not None:
            if c.raw.notice_period_days <= 30:
                score += 20.0
            else:
                penalty = (c.raw.notice_period_days - 30) * 0.5
                score -= min(penalty, 30.0)
                
        # 4. Activity Recency
        if c.raw.github_score and c.raw.github_score > 70:
            score += 10.0
            
        return min(max(score, 0.0), 100.0)
