# tests/test_career.py
import unittest
from schemas import RawCandidate, RawRole, ScoredCandidate
from stages.stage2_career import CareerCognitionStage

class TestCareerCognition(unittest.TestCase):
    def setUp(self):
        self.stage = CareerCognitionStage()

    def test_production_evidence_penalty(self):
        # Candidate claiming shipping without production evidence
        raw1 = RawCandidate(
            candidate_id="t1",
            name="A",
            title="Dev",
            years_experience=3.0,
            skills=[],
            roles=[
                RawRole(company="C", title="Dev", tenure_months=12, responsibilities=["shipped and deployed released features"])
            ],
            github_score=None,
            response_rate=None,
            notice_period_days=None,
            open_to_work=False,
            assessment_score=None
        )
        c1 = ScoredCandidate(raw=raw1, confidence_score=50.0)
        
        # Candidate with concrete evidence
        raw2 = RawCandidate(
            candidate_id="t2",
            name="B",
            title="Dev",
            years_experience=3.0,
            skills=[],
            roles=[
                RawRole(company="C", title="Dev", tenure_months=12, responsibilities=["shipped and deployed released features to production for 1M users"])
            ],
            github_score=None,
            response_rate=None,
            notice_period_days=None,
            open_to_work=False,
            assessment_score=None
        )
        c2 = ScoredCandidate(raw=raw2, confidence_score=50.0)
        
        results = self.stage.process([c1, c2])
        
        c1_res = next(c for c in results if c.raw.candidate_id == "t1")
        c2_res = next(c for c in results if c.raw.candidate_id == "t2")
        
        # Both should have some shipper score
        self.assertGreater(c1_res.career_vector.shipper, 0)
        self.assertGreater(c2_res.career_vector.shipper, 0)
        
        # C1 should have lower confidence due to missing production evidence
        self.assertLess(c1_res.confidence_score, c2_res.confidence_score)

if __name__ == "__main__":
    unittest.main()
