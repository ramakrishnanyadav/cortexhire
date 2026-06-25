import os
import json
import time
import tracemalloc
import logging
from collections import Counter
import sys

from data.loader import CandidateLoader
from pipeline import CortexHirePipeline
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("cortexhire.final_run")

def evaluate_large_dataset(jsonl_path: str, jd_path: str):
    logger.info(f"Starting final evaluation on massive dataset: {jsonl_path}")
    
    with open(jd_path, 'r') as f:
        jd_text = f.read()
        
    tracemalloc.start()
    start_time = time.time()
    
    # 1. Load Data
    logger.info("Loading candidates (this may take a moment and consume RAM)...")
    loader = CandidateLoader()
    
    # We will override the loader to track validation failures directly if needed,
    # but the loader already logs errors. Let's just track the output size.
    candidates = loader.load(jsonl_path)
    logger.info(f"Successfully loaded {len(candidates)} valid candidates.")
    
    # 2. Pipeline Execution
    logger.info("Executing Pipeline...")
    pipeline = CortexHirePipeline(jd_text=jd_text)
    
    # Let's temporarily increase config.FINAL_TOP_N so we can get distribution of top 1000 or all if we want,
    # but we can also just run it as is.
    # To get distribution of ALL candidates, we should patch the trust engine output.
    
    # We will manually run the stages to collect global distributions
    from schemas import ScoredCandidate
    scored_candidates = [ScoredCandidate(raw=c) for c in candidates]
    
    for stage in pipeline.stages:
        logger.info(f"Running stage: {stage.STAGE_NAME}...")
        scored_candidates = stage.run(scored_candidates)
        
    logger.info("Running Trust Engine...")
    for c in scored_candidates:
        pipeline.trust_engine.score(c)
        
    # Calculate distributions
    trust_scores = [c.trust_score for c in scored_candidates]
    confidence_scores = [c.confidence_score for c in scored_candidates]
    
    trust_dist = {
        "90-100": len([s for s in trust_scores if s >= 90]),
        "80-89": len([s for s in trust_scores if 80 <= s < 90]),
        "70-79": len([s for s in trust_scores if 70 <= s < 80]),
        "60-69": len([s for s in trust_scores if 60 <= s < 70]),
        "0-59": len([s for s in trust_scores if s < 60]),
    }
    
    conf_dist = {
        "80-100": len([s for s in confidence_scores if s >= 80]),
        "60-79": len([s for s in confidence_scores if 60 <= s < 80]),
        "40-59": len([s for s in confidence_scores if 40 <= s < 60]),
        "0-39": len([s for s in confidence_scores if s < 40]),
    }
    
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0
    avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    logger.info("Running Ranker...")
    config.FINAL_TOP_N = 20 # Only want top 20 for this output
    top_candidates = pipeline.ranker.rank(scored_candidates)
    
    end_time = time.time()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Print Metrics
    logger.info("="*50)
    logger.info("FINAL EVALUATION METRICS")
    logger.info("="*50)
    logger.info(f"Total Time: {end_time - start_time:.2f} seconds")
    logger.info(f"Peak Memory: {peak / 10**6:.2f} MB")
    logger.info(f"Candidates Processed: {len(scored_candidates)}")
    logger.info(f"Average Trust: {avg_trust:.2f}")
    logger.info(f"Average Confidence: {avg_conf:.2f}")
    
    logger.info("Trust Distribution:")
    for k, v in trust_dist.items(): logger.info(f"  {k}: {v}")
        
    logger.info("Confidence Distribution:")
    for k, v in conf_dist.items(): logger.info(f"  {k}: {v}")
        
    logger.info("\nTOP 20 CANDIDATES:")
    for i, c in enumerate(top_candidates):
        logger.info(f"#{i+1} {c.raw.name} | Score: {c.composite_score:.2f} | Conf: {c.confidence_score:.2f} | Trust: {c.trust_score:.2f}")
        
if __name__ == "__main__":
    evaluate_large_dataset(
        jsonl_path=r"C:\Users\Ramakrishna\OneDrive\Pictures\java\Documents\Projects\H2skill\India_runs_data_and_ai_challenge\candidates.jsonl",
        jd_path=r"C:\Users\Ramakrishna\OneDrive\Pictures\java\Documents\Projects\H2skill\cortexhire\jd.txt"
    )
