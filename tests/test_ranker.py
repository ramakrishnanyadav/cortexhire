# tests/test_ranker.py
import unittest
from schemas import RawCandidate, ScoredCandidate, CareerVector
from ranking.ranker import CompositeRanker

class TestCompositeRanker(unittest.TestCase):
    def setUp(self):
        self.ranker = CompositeRanker()

    def test_sigmoid_smoothing_and_tie_breaking(self):
        # Two identical candidates but different confidence
        c1 = ScoredCandidate(
            raw=RawCandidate("c1", "A", "Title", 5.0, [], [], None, None, None, True, None),
            career_vector=CareerVector(builder=45, shipper=40),
            eligibility_score=90.0,
            recruitability_score=80.0,
            trust_score=95.0,
            confidence_score=90.0,
            semantic_similarity=0.8
        )
        
        c2 = ScoredCandidate(
            raw=RawCandidate("c2", "B", "Title", 5.0, [], [], None, None, None, True, None),
            career_vector=CareerVector(builder=45, shipper=40),
            eligibility_score=90.0,
            recruitability_score=80.0,
            trust_score=95.0,
            confidence_score=40.0,
            semantic_similarity=0.8
        )
        
        top_n = self.ranker.rank([c1, c2])
        
        self.assertEqual(len(top_n), 2)
        # C1 should win the tie breaker due to higher confidence
        self.assertEqual(top_n[0].raw.candidate_id, "c1")
        self.assertEqual(top_n[1].raw.candidate_id, "c2")
        
        # Uncertainty interval should be larger for C2
        self.assertGreater(top_n[1].prediction_interval, top_n[0].prediction_interval)

if __name__ == "__main__":
    unittest.main()
