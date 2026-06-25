# tests/test_trust.py
import unittest
from schemas import RawCandidate, RawRole, ScoredCandidate
from trust.engine import TrustEngine

class TestTrustEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TrustEngine()

    def test_career_changer_bypass(self):
        raw = RawCandidate(
            candidate_id="test1",
            name="Alice",
            title="Senior ML Engineer",
            years_experience=5.0,
            skills=["pytorch", "tensorflow", "kubernetes"],
            roles=[
                RawRole(company="A", title="Marketing Manager", tenure_months=24, responsibilities=[]),
                RawRole(company="B", title="Data Scientist", tenure_months=18, responsibilities=[])
            ],
            github_score=85,
            response_rate=0.9,
            notice_period_days=30,
            open_to_work=True,
            assessment_score=None
        )
        scored = ScoredCandidate(raw=raw)
        result = self.engine.score(scored)
        
        # Should have bypass and consistent high trust
        self.assertGreaterEqual(result.trust_score, 100.0)
        self.assertGreater(result.confidence_score, 50.0)

    def test_skill_explosion_penalty(self):
        raw = RawCandidate(
            candidate_id="test2",
            name="Bob",
            title="AI Expert",
            years_experience=1.0,
            skills=["pytorch", "tensorflow", "transformers", "fine-tuning", "rlhf", "langchain", "vector db", "faiss", "milvus", "pinecone", "rag", "llm", "embedding", "mlflow", "kubeflow", "triton", "cuda", "onnx", "bert"],
            roles=[
                RawRole(company="A", title="AI Engineer", tenure_months=6, responsibilities=[])
            ],
            github_score=10,
            response_rate=0.9,
            notice_period_days=30,
            open_to_work=True,
            assessment_score=None
        )
        scored = ScoredCandidate(raw=raw)
        result = self.engine.score(scored)
        
        # Should penalize trust and confidence due to explosion
        self.assertTrue(any(f.flag_type == "skill_explosion" for f in result.trust_flags))
        self.assertLess(result.trust_score, 80.0)

if __name__ == "__main__":
    unittest.main()
