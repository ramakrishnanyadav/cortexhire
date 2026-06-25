# pipeline.py
from __future__ import annotations
import time
import logging
from dataclasses import dataclass

from schemas import RawCandidate, ScoredCandidate
from stages.stage1_eligibility import EligibilityStage
from stages.stage2_career import CareerCognitionStage
from stages.stage3_semantic import SemanticMatchingStage
from stages.stage4_recruitability import RecruitabilityStage
from trust.engine import TrustEngine
from ranking.ranker import CompositeRanker

logger = logging.getLogger("cortexhire.pipeline")

@dataclass
class PipelineMetrics:
    total_candidates: int = 0
    average_confidence: float = 0.0
    average_trust: float = 0.0
    stage_latencies_ms: dict[str, float] | None = None

@dataclass
class PipelineResult:
    top_candidates: list[ScoredCandidate]
    execution_time_ms: float
    metrics: PipelineMetrics

class CortexHirePipeline:
    def __init__(self, jd_text: str):
        self.stages = [
            EligibilityStage(),
            CareerCognitionStage(),
            SemanticMatchingStage(jd_text),
            RecruitabilityStage(),
        ]
        self.trust_engine = TrustEngine()
        self.ranker = CompositeRanker()

    def run(self, raw_candidates: list[RawCandidate]) -> PipelineResult:
        logger.info(f"Starting CortexHire pipeline for {len(raw_candidates)} candidates.")
        start_total = time.time()
        
        candidates = [ScoredCandidate(raw=c) for c in raw_candidates]
        stage_latencies = {}

        # 1. Execute cognitive stages
        for stage in self.stages:
            stage_start = time.time()
            candidates = stage.run(candidates)
            stage_latencies[stage.STAGE_NAME] = (time.time() - stage_start) * 1000

        # 2. Execute Trust & Uncertainty Engine
        trust_start = time.time()
        candidates = [self.trust_engine.score(c) for c in candidates]
        stage_latencies["Trust Engine"] = (time.time() - trust_start) * 1000

        # Calculate pre-ranking observability metrics
        avg_confidence = sum(c.confidence_score for c in candidates) / len(candidates) if candidates else 0.0
        avg_trust = sum(c.trust_score for c in candidates) / len(candidates) if candidates else 0.0

        # 3. Final Ranking
        rank_start = time.time()
        top_candidates = self.ranker.rank(candidates)
        stage_latencies["Ranking"] = (time.time() - rank_start) * 1000

        execution_time_ms = (time.time() - start_total) * 1000
        
        logger.info("--- CortexHire Execution Metrics ---")
        for stage_name, ms in stage_latencies.items():
            logger.info(f"  {stage_name}: {ms:.2f} ms")
        logger.info(f"Average Confidence: {avg_confidence:.2f}")
        logger.info(f"Average Trust: {avg_trust:.2f}")
        logger.info(f"Total Pipeline Latency: {execution_time_ms:.2f} ms")

        metrics = PipelineMetrics(
            total_candidates=len(raw_candidates),
            average_confidence=avg_confidence,
            average_trust=avg_trust,
            stage_latencies_ms=stage_latencies
        )

        return PipelineResult(
            top_candidates=top_candidates,
            execution_time_ms=execution_time_ms,
            metrics=metrics
        )
