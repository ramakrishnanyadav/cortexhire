# evaluation/metrics.py
from __future__ import annotations
from schemas import PipelineResult

class EvaluationEngine:
    """
    Computes ranking metrics for the run.
    """
    def compute(self, result: PipelineResult) -> dict[str, float]:
        """
        In a full implementation, this would compute NDCG, Precision@K,
        and trap rejection rate against a ground truth dataset.
        For this stub, we compute basic pool statistics.
        """
        total = result.total_input
        if total == 0:
            return {"survival_rate": 0.0}
            
        return {
            "survival_rate": round(len(result.top_candidates) / total, 3),
            "stage1_elimination_rate": self._elimination_rate(result, "Eligibility Intelligence", total),
            "trust_flag_density": self._trust_flag_density(result.top_candidates)
        }
        
    def _elimination_rate(self, result: PipelineResult, stage_name: str, total: int) -> float:
        survivors = result.stage_counts.get(stage_name, total)
        return round(1.0 - (survivors / total), 3)
        
    def _trust_flag_density(self, candidates) -> float:
        if not candidates: return 0.0
        total_flags = sum(len(c.trust_flags) for c in candidates)
        return round(total_flags / len(candidates), 2)
