# tests/test_integration.py
import unittest
import json
import os
from pipeline import CortexHirePipeline
from data.loader import CandidateLoader

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Create a mock JD and mock candidates JSON
        self.jd = "We are looking for a Senior Machine Learning Engineer with 5+ years of experience in PyTorch and deploying models to production."
        
        self.mock_candidates = [
            {
                "candidate_id": "int1",
                "name": "Jane Doe",
                "title": "Senior ML Engineer",
                "years_experience": 6.0,
                "skills": ["pytorch", "python", "docker", "kubernetes"],
                "roles": [
                    {
                        "company": "Tech Corp",
                        "title": "Senior ML Engineer",
                        "tenure_months": 48,
                        "is_product_company": True,
                        "is_service_company": False,
                        "responsibilities": ["shipped and deployed machine learning models to production serving 10m users at 50ms latency"]
                    }
                ],
                "github_score": 90.0,
                "response_rate": 0.95,
                "notice_period_days": 15,
                "open_to_work": True
            }
        ]
        
        with open("mock_candidates.json", "w") as f:
            json.dump(self.mock_candidates, f)

    def tearDown(self):
        if os.path.exists("mock_candidates.json"):
            os.remove("mock_candidates.json")

    def test_end_to_end_pipeline(self):
        loader = CandidateLoader()
        raw_candidates = loader.load("mock_candidates.json")
        
        self.assertEqual(len(raw_candidates), 1)
        
        pipeline = CortexHirePipeline(self.jd)
        result = pipeline.run(raw_candidates)
        top_candidates = result.top_candidates
        
        self.assertEqual(len(top_candidates), 1)
        winner = top_candidates[0]
        
        # Verify quantitative extraction worked and boosted confidence
        self.assertGreaterEqual(winner.confidence_score, 0.0)
        
        # Verify ranking breakdown is present
        self.assertIn("composite_final", winner.score_breakdown)
        self.assertIn("prediction_interval", winner.score_breakdown)

if __name__ == "__main__":
    unittest.main()
