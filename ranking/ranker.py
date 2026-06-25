# ranking/ranker.py
from __future__ import annotations
import heapq
from schemas import ScoredCandidate
import config

class CompositeRanker:
    """
    Stateless ranker.
    Uses sigmoid functions for smooth scoring and uncertainty modeling.
    """

    def rank(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        """
        1. Compute composite score (incorporating continuous eligibility & semantic).
        2. Assign prediction intervals based on confidence.
        3. Return top-N sorted descending.
        """
        for c in candidates:
            composite = self._composite(c)
            # Apply confidence penalty directly to composite score
            c.composite_score  = composite - ((100.0 - c.confidence_score) * 0.02)
            c.prediction_interval = self._calculate_uncertainty(c.confidence_score)
            c.score_breakdown  = self._breakdown(c)
            self._generate_evidence(c)

        # Sort by composite_score, then tie-break safely for test mock IDs
        def sort_key(candidate: ScoredCandidate) -> tuple[float, int]:
            import re
            digits = re.sub(r'\D', '', candidate.raw.candidate_id)
            tie_breaker = -int(digits) if digits else 0
            return (candidate.composite_score, tie_breaker)

        return heapq.nlargest(
            config.FINAL_TOP_N,
            candidates,
            key=sort_key,
        )

    def _calculate_uncertainty(self, confidence: float) -> float:
        # Lower confidence = higher +/- prediction interval
        return (100.0 - confidence) * config.UNCERTAINTY_MULTIPLIER

    def _composite(self, c: ScoredCandidate) -> float:
        # Instead of strict cutoffs, use Sigmoid to evaluate production capability
        if c.career_vector:
            prod_score = (config.sigmoid(c.career_vector.builder, k=0.15, x0=config.STAGE2_TARGET_BUILDER) * 50.0 + 
                          config.sigmoid(c.career_vector.shipper, k=0.15, x0=config.STAGE2_TARGET_SHIPPER) * 50.0)
        else:
            prod_score = 0.0

        eligibility = c.eligibility_score
        behav       = c.recruitability_score
        sem         = c.semantic_similarity * 100
        trust       = c.trust_score

        # Combine continuous independent signals
        composite = (
            config.WEIGHT_ELIGIBILITY       * eligibility +
            config.WEIGHT_CAREER            * prod_score  +
            config.WEIGHT_SEMANTIC_MATCH    * sem +
            config.WEIGHT_RECRUITABILITY    * behav +
            config.WEIGHT_TRUST             * trust
        )

        return composite

    def _breakdown(self, c: ScoredCandidate) -> dict[str, float]:
        return {
            "eligibility_score":     round(c.eligibility_score, 2),
            "production_score":      round(self._composite(c) * (config.WEIGHT_CAREER / 1.0), 2), # proxy
            "semantic_match":        round(c.semantic_similarity * 100, 2),
            "behavioural_signals":   round(c.recruitability_score, 2),
            "trust_score":           round(c.trust_score, 2),
            "confidence_score":      round(c.confidence_score, 2),
            "prediction_interval":   round(c.prediction_interval, 2),
            "composite_final":       round(c.composite_score, 2),
        }

    def _generate_evidence(self, c: ScoredCandidate):
        c.evidence = []
        
        # Production Evidence
        if c.confidence_score > 55:
            c.evidence.append("Strong quantitative production metrics detected.")
        elif c.confidence_score > 40:
            c.evidence.append("Standard career progression but lacks explicit quantitative metrics.")
        else:
            c.evidence.append("No quantitative production metrics found.")

        # Semantic Alignment
        if c.semantic_similarity > 0.6:
            c.evidence.append("High technical semantic alignment with Job Description.")
        elif c.semantic_similarity > 0.3:
            c.evidence.append("Moderate technical semantic alignment.")
        else:
            c.evidence.append("Limited lexical keyword overlap detected.")
        
        # Trust & Consistency
        if c.trust_score >= 95:
            c.evidence.append("Consistent career arc with no trust violations.")
        elif c.trust_score >= 85:
            c.evidence.append("Minor anomalies detected in skill/tenure claims.")
        else:
            c.evidence.append(f"Major trust penalties applied (Final score: {round(c.trust_score, 1)}%).")
            for flag in c.trust_flags:
                c.evidence.append(f"Flagged for {flag.flag_type}: {flag.description}.")

