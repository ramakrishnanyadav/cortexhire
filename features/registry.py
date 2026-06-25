# features/registry.py
from __future__ import annotations
from features.base import FeatureExtractor

class FeatureExtractorRegistry:
    """
    Central registry for all feature extractors.
    Ensures every extractor is registered exactly once.
    Supports versioned lookup for audit trails.

    Data structure: dict[str, FeatureExtractor]
    Access: O(1) lookup by name
    """
    _registry: dict[str, FeatureExtractor] = {}

    @classmethod
    def register(cls, name: str, extractor: FeatureExtractor) -> None:
        if name in cls._registry:
            raise ValueError(f"Extractor '{name}' already registered. Use update() to replace.")
        cls._registry[name] = extractor

    @classmethod
    def get(cls, name: str) -> FeatureExtractor:
        if name not in cls._registry:
            raise KeyError(f"No extractor registered under '{name}'")
        return cls._registry[name]

    @classmethod
    def all_extractors(cls) -> list[tuple[str, FeatureExtractor]]:
        return list(cls._registry.items())

    @classmethod
    def versions(cls) -> dict[str, str]:
        return {name: ext.VERSION for name, ext in cls._registry.items()}
