# trust/engine.py
from __future__ import annotations
from schemas import ScoredCandidate, RawCandidate, TrustFlag
import config

_ML_SKILL_KEYWORDS = frozenset({
    "pytorch", "tensorflow", "transformers", "fine-tuning", "rlhf",
    "langchain", "vector db", "faiss", "milvus", "pinecone",
    "rag", "llm", "embedding", "mlflow", "kubeflow", "triton",
    "cuda", "onnx", "bert", "gpt", "attention", "diffusion",
})

_NON_TECHNICAL_TITLE_TOKENS = frozenset({
    "marketing", "operations", "hr", "recruiter", "accountant",
    "sales", "legal", "finance", "analyst", "business",
})

class TrustEngine:
    """
    Stateless scorer.
    Returns the ScoredCandidate with trust_score and trust_flags populated.
    """

    def score(self, candidate: ScoredCandidate) -> ScoredCandidate:
        raw    = candidate.raw
        flags  = []
        points = 100.0
        # Incorporate existing confidence modifiers (e.g. from eligibility sparse data)
        confidence = config.CONFIDENCE_BASE + candidate.confidence_score
        # Add continuous variance to prevent quantization
        # Using response rate, skill count, and role tenure to create a unique float fingerprint per candidate
        response_penalty = (1.0 - (raw.response_rate or 0.5)) * 5.0
        skill_variance = min(len(raw.skills) * 0.15, 4.0)  # Slight penalty for listing massive keyword lists
        points -= (response_penalty + skill_variance)
        
        # Granular confidence spread based on experience depth and role stability
        tenure_stability = sum(r.tenure_months for r in raw.roles) / max(len(raw.roles), 1)
        confidence += min((raw.years_experience * 1.2), 15.0)
        confidence += min((tenure_stability * 0.1), 5.0)

        # ── Penalties ─────────────────────────────────────────────────────
        mismatch_flag = self._check_title_skill_mismatch(raw)
        if mismatch_flag and not self._career_changer_bypass(raw):
            flags.append(mismatch_flag)
            points -= config.TRUST_PENALTY_TITLE_SKILL_MISMATCH
            confidence -= 10.0

        explosion_flag = self._check_skill_explosion(raw)
        if explosion_flag:
            flags.append(explosion_flag)
            points -= config.TRUST_PENALTY_SKILL_EXPLOSION
            confidence -= 15.0

        consulting_flag = self._check_consulting_disguise(raw)
        if consulting_flag:
            flags.append(consulting_flag)
            points -= config.TRUST_PENALTY_CONSULTING_DISGUISE
            confidence -= 5.0

        # ── Boosts ────────────────────────────────────────────────────────
        if raw.github_score and raw.github_score >= 60:
            points += config.TRUST_BOOST_GITHUB_CORROBORATION
            confidence += 15.0
            flags.append(TrustFlag(
                flag_type="github_corroboration",
                description="Active GitHub presence corroborates claimed skills",
                penalty=-config.TRUST_BOOST_GITHUB_CORROBORATION,
                evidence=f"github_score={raw.github_score:.1f}",
            ))

        if self._has_consistent_arc(raw):
            points += config.TRUST_BOOST_CONSISTENT_ARC
            confidence += 10.0

        if self._career_changer_bypass(raw):
            points += config.TRUST_BOOST_CAREER_CHANGER_BYPASS
            confidence += 10.0

        candidate.trust_score  = max(0.0, min(100.0, points))
        candidate.confidence_score = max(0.0, min(100.0, confidence))
        candidate.trust_flags  = flags
        return candidate

    def _check_title_skill_mismatch(self, raw: RawCandidate) -> TrustFlag | None:
        import re
        title_tokens = set(re.findall(r"\b[a-zA-Z]+\b", raw.title.lower()))
        has_non_tech_title = bool(title_tokens.intersection(_NON_TECHNICAL_TITLE_TOKENS))
        ml_skill_count     = len(_ML_SKILL_KEYWORDS.intersection(
            s.lower() for s in raw.skills
        ))
        if has_non_tech_title and ml_skill_count >= 5:
            return TrustFlag(
                flag_type="title_skill_mismatch",
                description=(
                    f"Non-technical title '{raw.title}' claims {ml_skill_count} advanced ML skills"
                ),
                penalty=config.TRUST_PENALTY_TITLE_SKILL_MISMATCH,
                evidence=f"title={raw.title}, ml_skills={ml_skill_count}",
            )
        return None

    def _check_skill_explosion(self, raw: RawCandidate) -> TrustFlag | None:
        ml_skill_count = len(_ML_SKILL_KEYWORDS.intersection(
            s.lower() for s in raw.skills
        ))
        ml_tenure_months = sum(
            r.tenure_months for r in raw.roles
            if any(kw in r.title.lower() for kw in {"ml", "ai", "data", "machine learning"})
        )
        if ml_skill_count > 15 and ml_tenure_months < 18:
            return TrustFlag(
                flag_type="skill_explosion",
                description=(
                    f"{ml_skill_count} ML skills claimed with only {ml_tenure_months}mo ML tenure"
                ),
                penalty=config.TRUST_PENALTY_SKILL_EXPLOSION,
                evidence=f"ml_skills={ml_skill_count}, ml_tenure_months={ml_tenure_months}",
            )
        return None

    def _check_consulting_disguise(self, raw: RawCandidate) -> TrustFlag | None:
        if not raw.roles: return None
        all_companies_consulting = all(r.is_service_company for r in raw.roles)
        claims_product_ownership = any(
            "product" in resp.lower() or "owned" in resp.lower()
            for role in raw.roles
            for resp in role.responsibilities
        )
        if all_companies_consulting and claims_product_ownership:
            return TrustFlag(
                flag_type="consulting_disguise",
                description="All roles at service/consulting firms; 'product ownership' claim unsubstantiated",
                penalty=config.TRUST_PENALTY_CONSULTING_DISGUISE,
                evidence=f"companies={[r.company for r in raw.roles]}",
            )
        return None

    def _has_consistent_arc(self, raw: RawCandidate) -> bool:
        seniority_map = {
            "intern": 0, "junior": 1, "associate": 1, "engineer": 2,
            "senior": 3, "staff": 4, "principal": 5, "director": 6,
        }
        levels = []
        for role in raw.roles:
            title_lower = role.title.lower()
            for keyword, level in sorted(seniority_map.items(), key=lambda x: -x[1]):
                if keyword in title_lower:
                    levels.append(level)
                    break
        if len(levels) < 2:
            return False
        return all(levels[i] <= levels[i + 1] for i in range(len(levels) - 1))

    def _career_changer_bypass(self, raw: RawCandidate) -> bool:
        """
        Transition Detection: Uses role shift velocity and recent technical evidence.
        """
        if not raw.github_score or raw.github_score < 40:
            return False
            
        # Role shift velocity
        ml_tenure_months = sum(
            r.tenure_months for r in raw.roles
            if any(kw in r.title.lower() for kw in {"ml", "ai", "machine learning", "data scientist"})
        )
        return ml_tenure_months >= 12 # Softened threshold for robust transition detection
