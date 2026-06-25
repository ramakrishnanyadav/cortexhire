# stages/stage3_semantic.py
from __future__ import annotations
import logging
from stages.base import PipelineStage
from schemas import ScoredCandidate
import config

logger = logging.getLogger("cortexhire.stage3")

class SemanticMatchingStage(PipelineStage):
    STAGE_NUMBER = 3
    STAGE_NAME   = "Asymmetric Semantic Retrieval Engine"

    def __init__(self, jd_text: str):
        super().__init__()
        self.jd_text = jd_text
        self.model = None
        self.index = None
        self.candidate_ids = []
        self._load_model()

    def _load_model(self):
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading Asymmetric Semantic Model: {config.EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(config.EMBEDDING_MODEL)
            # Use Inner Product (Cosine Similarity since embeddings will be normalized)
            self.index = faiss.IndexFlatIP(config.EMBEDDING_DIM)
            self.faiss = faiss
        except ImportError:
            logger.warning("faiss or sentence-transformers not found. Using fallback heuristic.")
            self.model = None

    def process(self, candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
        if not candidates:
            return []

        if not self.model:
            self._fallback_process(candidates)
            return candidates

        import numpy as np

        logger.info("Computing JD embedding...")
        jd_embedding = self.model.encode([self.jd_text], normalize_embeddings=True)

        logger.info("Computing sectional candidate embeddings...")
        
        # Section-level embeddings to reduce noise
        for c in candidates:
            skills_text = " ".join(c.raw.skills)
            roles_text = " ".join([f"{r.title} {r.company} " + " ".join(r.responsibilities) for r in c.raw.roles])
            
            # If no skills or roles, use empty string
            if not skills_text: skills_text = "none"
            if not roles_text: roles_text = "none"
            
            # Create two separate embeddings
            embeddings = self.model.encode([skills_text, roles_text], normalize_embeddings=True)
            
            # Weighted average: 40% skills, 60% experience
            final_embedding = (embeddings[0] * 0.4) + (embeddings[1] * 0.6)
            
            # Normalize the resulting averaged embedding
            final_embedding = final_embedding / np.linalg.norm(final_embedding)
            
            self.index.add(np.array([final_embedding], dtype=np.float32))
            self.candidate_ids.append(c.raw.candidate_id)

        logger.info("Performing FAISS retrieval...")
        k = min(config.STAGE3_TOP_K, len(candidates))
        distances, indices = self.index.search(jd_embedding, k)

        # Map FAISS distances (cosine similarity) back to candidates
        score_map = {}
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:
                cid = self.candidate_ids[idx]
                score_map[cid] = float(dist)

        for c in candidates:
            c.semantic_similarity = score_map.get(c.raw.candidate_id, 0.0)

        return candidates

    def _fallback_process(self, candidates: list[ScoredCandidate]) -> None:
        import re
        jd_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", self.jd_text.lower()))
        stop_words = {"and", "the", "with", "for", "are", "you", "will", "this", "that", "from", "have", "not", "your", "our", "all", "any", "can", "but", "about", "more", "has", "who", "which"}
        jd_tokens = jd_tokens - stop_words
        if not jd_tokens: return

        for c in candidates:
            c_text = " ".join(c.raw.skills) + " ".join(r.title + " " + " ".join(r.responsibilities) for r in c.raw.roles)
            c_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", c_text.lower()))
            intersection = jd_tokens.intersection(c_tokens)
            
            # Use Overlap Coefficient instead of Jaccard
            overlap = len(intersection) / len(jd_tokens) if len(jd_tokens) > 0 else 0.0
            
            # Give a strong boost if job title matches any candidate role title
            title_boost = 0.0
            for r in c.raw.roles:
                role_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", r.title.lower()))
                title_intersection = jd_tokens.intersection(role_tokens)
                if len(title_intersection) >= 2:
                    title_boost = 0.5
                    break
            
            c.semantic_similarity = min(overlap + title_boost, 1.0)
