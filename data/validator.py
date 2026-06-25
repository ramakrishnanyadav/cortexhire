# data/validator.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class RoleModel(BaseModel):
    company: str
    title: str
    tenure_months: int = Field(ge=0)
    is_product_company: Optional[bool] = False
    is_service_company: Optional[bool] = False
    responsibilities: List[str] = []

class CandidateModel(BaseModel):
    candidate_id: str
    name: str
    title: str
    years_experience: float = Field(ge=0.0)
    skills: List[str] = []
    roles: List[RoleModel] = []
    github_score: Optional[float] = None
    response_rate: Optional[float] = None
    notice_period_days: Optional[int] = None
    open_to_work: bool = False
    assessment_score: Optional[float] = None
