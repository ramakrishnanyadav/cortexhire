# features/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from schemas import RawCandidate, ScoredCandidate

class FeatureExtractor(ABC):
    """
    Abstract base for all feature extractors.
    Every extractor MUST be stateless — same input → same output.
    O(1) per candidate unless documented otherwise.
    """
    VERSION: str = "1.0.0"

    @abstractmethod
    def extract(self, candidate: RawCandidate) -> dict[str, float]:
        """
        Returns a flat dict of feature_name → float (always 0.0–100.0 range).
        Must never raise; return 0.0 for missing data.
        """
        ...

    @abstractmethod
    def feature_names(self) -> list[str]:
        """All feature keys this extractor can produce."""
        ...
