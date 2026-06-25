# stages/stage5_reasoning.py
from __future__ import annotations
from stages.base import PipelineStage
from schemas import ScoredCandidate, EvidenceItem

class ReasoningStage(PipelineStage):
    STAGE_NUMBER = 5
    STAGE_NAME   = "Evidence Generator Engine"

    def process(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        """
        Generate evidence items explaining why a candidate scored the way they did.
        """
        for c in candidates:
            evidence_list = []
            
            if c.career_vector and c.career_vector.builder > 50:
                evidence_list.append(EvidenceItem(
                    dimension="production_experience",
                    signal=f"Strong builder signals detected (Score: {c.career_vector.builder:.1f})",
                    weight=0.3,
                    source="career_vector_extraction"
                ))
                
            if c.raw.github_score and c.raw.github_score >= 60:
                 evidence_list.append(EvidenceItem(
                    dimension="technical_depth",
                    signal=f"High GitHub score validates skills ({c.raw.github_score})",
                    weight=0.15,
                    source="github_metrics"
                ))

            c.evidence = evidence_list
            
        return candidates
