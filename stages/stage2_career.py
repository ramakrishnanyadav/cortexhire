# stages/stage2_career.py
from __future__ import annotations
import re
from stages.base import PipelineStage
from schemas import ScoredCandidate, CareerVector
import config

_BUILDER_SIGNALS   = frozenset({"built", "developed", "created", "designed", "architected", "launched", "owned", "led"})
_SHIPPER_SIGNALS   = frozenset({"deployed", "shipped", "released", "rolled", "live", "end-to-end", "delivered"})
_RESEARCHER_SIGNALS= frozenset({"paper", "research", "experiment", "ablation", "benchmark", "arxiv", "published", "phd", "thesis", "academic"})
_CONSULTANT_SIGNALS= frozenset({"advised", "consulting", "client", "engagement", "proposal", "stakeholder", "requirements"})
_MANAGER_SIGNALS   = frozenset({"managed", "reports", "hiring", "roadmap", "okr", "budget", "headcount", "performance"})
_LEADER_SIGNALS    = frozenset({"staff", "principal", "lead", "architecture", "rfc", "design", "mentored", "platform"})

_PRODUCTION_EVIDENCE = frozenset({"production", "users", "scale", "customers", "latency", "throughput", "slas", "uptime"})

class CareerCognitionStage(PipelineStage):
    STAGE_NUMBER = 2
    STAGE_NAME   = "Career Cognition Engine"

    def process(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        """
        Calculates career vectors and applies quantitative evidence extraction.
        """
        for c in candidates:
            vec = self._compute_career_vector(c.raw)
            c.career_vector = vec
            
            # Extract quantitative evidence (e.g. 10M users, 50ms, 99.9%)
            quant_matches = self._extract_quantitative_evidence(c.raw)
            has_quant = len(quant_matches) > 0
            
            # Check for generic production words
            has_prod = self._has_production_evidence(c.raw)
            
            # Confidence penalty for claiming shipper without evidence
            if vec.shipper > 20:
                if not has_prod and not has_quant:
                    c.confidence_score -= 20.0
                elif has_prod and not has_quant:
                    c.confidence_score -= 5.0 # Better, but lacks hard numbers
                elif has_quant:
                    c.confidence_score += 10.0 # Excellent, provided quantitative metrics!

        return candidates

    def _extract_quantitative_evidence(self, raw) -> list[str]:
        """
        Regex extraction of quantitative achievements.
        Examples: 10M users, 50ms latency, 99.9% SLA, 100k requests
        """
        matches = []
        pattern = r"\b(\d+(?:\.\d+)?(?:k|m|b|ms|s|%|\+)?\s*(?:users|requests|latency|sla|uptime|revenue|reduction|improvement))\b"
        
        for role in raw.roles:
            text = " ".join([role.title] + role.responsibilities).lower()
            found = re.findall(pattern, text)
            matches.extend(found)
        return matches

    def _has_production_evidence(self, raw) -> bool:
        for role in raw.roles:
            text = " ".join([role.title] + role.responsibilities).lower()
            text_tokens = set(re.findall(r"\b[a-zA-Z]+\b", text))
            if _PRODUCTION_EVIDENCE.intersection(text_tokens):
                return True
        return False

    def _compute_career_vector(self, raw) -> CareerVector:
        counters = {
            "builder":    0, "shipper":    0, "researcher": 0,
            "consultant": 0, "manager":    0, "leader":     0,
        }
        signal_map = {
            "builder": _BUILDER_SIGNALS, "shipper": _SHIPPER_SIGNALS,
            "researcher": _RESEARCHER_SIGNALS, "consultant": _CONSULTANT_SIGNALS,
            "manager": _MANAGER_SIGNALS, "leader": _LEADER_SIGNALS,
        }

        for role in raw.roles:
            text = " ".join([role.title] + role.responsibilities).lower()
            text_tokens = set(re.findall(r"\b[a-zA-Z]+\b", text))
            for dimension, signals in signal_map.items():
                counters[dimension] += len(signals.intersection(text_tokens))

        _MAX_HITS = 8
        return CareerVector(
            builder    = min(counters["builder"]    / _MAX_HITS * 100, 100),
            shipper    = min(counters["shipper"]    / _MAX_HITS * 100, 100),
            researcher = min(counters["researcher"] / _MAX_HITS * 100, 100),
            consultant = min(counters["consultant"] / _MAX_HITS * 100, 100),
            manager    = min(counters["manager"]    / _MAX_HITS * 100, 100),
            leader     = min(counters["leader"]     / _MAX_HITS * 100, 100),
        )
