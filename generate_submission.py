import os
import time
import logging
import csv

from data.loader import CandidateLoader
from pipeline import CortexHirePipeline
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("cortexhire.submission")

def generate_submission(jsonl_path: str, jd_path: str, output_csv: str):
    logger.info(f"Loading candidates from {jsonl_path}")
    
    with open(jd_path, 'r') as f:
        jd_text = f.read()
        
    loader = CandidateLoader()
    candidates = loader.load(jsonl_path)
    
    logger.info("Running CortexHire Pipeline...")
    pipeline = CortexHirePipeline(jd_text=jd_text)
    
    from schemas import ScoredCandidate
    scored_candidates = [ScoredCandidate(raw=c) for c in candidates]
    
    for stage in pipeline.stages:
        scored_candidates = stage.run(scored_candidates)
        
    for c in scored_candidates:
        pipeline.trust_engine.score(c)
        
    logger.info("Ranking top 100 candidates...")
    config.FINAL_TOP_N = 100
    top_candidates = pipeline.ranker.rank(scored_candidates)
    
    # Enforce strict validation rules: score (rounded to 4 decimal places) descending, then candidate_id ascending
    top_candidates.sort(key=lambda c: (-round(c.composite_score / 100.0, 4), c.raw.candidate_id))
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for i, c in enumerate(top_candidates):
            evidence_str = " ".join(c.evidence) if c.evidence else "No specific evidence found."
            # Format: Title with X yrs; Conf: Y; Trust: Z. [Evidence]
            reasoning = f"{c.raw.title} with {c.raw.years_experience} yrs; Confidence: {round(c.confidence_score, 1)}%; Trust: {round(c.trust_score, 1)}%. {evidence_str}"
            score = round(c.composite_score / 100.0, 4)
            writer.writerow([c.raw.candidate_id, i+1, score, reasoning])
            
    logger.info(f"Submission saved to {output_csv}")

if __name__ == "__main__":
    generate_submission(
        jsonl_path=r"C:\Users\Ramakrishna\OneDrive\Pictures\java\Documents\Projects\H2skill\cortexhire\doc\candidates.jsonl",
        jd_path=r"C:\Users\Ramakrishna\OneDrive\Pictures\java\Documents\Projects\H2skill\cortexhire\jd.txt",
        output_csv=r"C:\Users\Ramakrishna\OneDrive\Pictures\java\Documents\Projects\H2skill\cortexhire\outputs\ranked_candidates.csv"
    )
