# stages/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from schemas import ScoredCandidate
import logging
import time

logger = logging.getLogger("cortexhire.pipeline")

class PipelineStage(ABC):
    """
    Abstract base for all five pipeline stages.

    Contract:
    - Input:  list[ScoredCandidate]
    - Output: list[ScoredCandidate]  (subset or same, never empty unless truly empty input)
    - Eliminated candidates MUST have stage_eliminated set
    - All stages are deterministic (no random state)
    - All stages log: input_count, output_count, elapsed_ms
    """
    STAGE_NUMBER: int
    STAGE_NAME: str

    @abstractmethod
    def process(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        ...

    def run(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        """Wraps process() with timing + logging. Do not override."""
        t0 = time.perf_counter()
        result = self.process(candidates)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            f"[Stage {self.STAGE_NUMBER}] {self.STAGE_NAME}: "
            f"{len(candidates)} -> {len(result)} ({elapsed:.1f}ms)"
        )
        return result
