# data/loader.py
from __future__ import annotations
import json
import logging
from schemas import RawCandidate, RawRole
from data.validator import CandidateModel

logger = logging.getLogger("cortexhire.loader")

class CandidateLoader:
    def load(self, filepath: str) -> list[RawCandidate]:
        """
        Loads raw candidates from a JSON or JSONL file.
        Maps Hackathon schema to CortexHire internal schema.
        """
        candidates_raw = []
        try:
            with open(filepath, 'r') as f:
                if filepath.endswith('.jsonl'):
                    for line in f:
                        if line.strip():
                            candidates_raw.append(json.loads(line))
                else:
                    candidates_raw = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {filepath}: {e}")
            return []
            
        candidates = []
        for c in candidates_raw:
            try:
                # 1. Map Hackathon Schema to our Internal Schema format
                mapped = {}
                mapped["candidate_id"] = c.get("candidate_id", "UNKNOWN")
                
                profile = c.get("profile", {})
                mapped["name"] = profile.get("anonymized_name", "Unknown")
                mapped["title"] = profile.get("current_title", "Unknown")
                mapped["years_experience"] = float(profile.get("years_of_experience", 0.0))
                
                # We can extract skills from headline or summary if available, but for now we leave empty
                # because the quantitative/career engine mostly looks at roles.responsibilities
                mapped["skills"] = [] 
                
                mapped_roles = []
                for r in c.get("career_history", []):
                    # Guess if product or service company based on industry
                    industry = r.get("industry", "").lower()
                    is_service = any(x in industry for x in ["it services", "consulting", "staffing"])
                    
                    mapped_roles.append({
                        "company": r.get("company", "Unknown"),
                        "title": r.get("title", "Unknown"),
                        "tenure_months": r.get("duration_months", 0),
                        "is_product_company": not is_service,
                        "is_service_company": is_service,
                        "responsibilities": [r.get("description", "")]
                    })
                mapped["roles"] = mapped_roles
                
                # Mock Behavioral Data since hackathon candidates don't have it natively in this JSON
                mapped["github_score"] = None
                mapped["response_rate"] = None
                mapped["notice_period_days"] = None
                mapped["open_to_work"] = False
                
                # 2. Pydantic Validation
                valid_model = CandidateModel.model_validate(mapped)
                
                # 3. Map to internal RawCandidate
                roles = [
                    RawRole(
                        company=r.company,
                        title=r.title,
                        tenure_months=r.tenure_months,
                        is_product_company=r.is_product_company,
                        is_service_company=r.is_service_company,
                        responsibilities=r.responsibilities
                    ) for r in valid_model.roles
                ]
                
                candidates.append(RawCandidate(
                    candidate_id=valid_model.candidate_id,
                    name=valid_model.name,
                    title=valid_model.title,
                    years_experience=valid_model.years_experience,
                    skills=valid_model.skills,
                    roles=roles,
                    github_score=valid_model.github_score,
                    response_rate=valid_model.response_rate,
                    notice_period_days=valid_model.notice_period_days,
                    open_to_work=valid_model.open_to_work,
                    assessment_score=valid_model.assessment_score
                ))
            except Exception:
                logger.exception(f"Validation failed for candidate {c.get('candidate_id', 'UNKNOWN')}")
            
        return candidates
