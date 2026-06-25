# main.py
from __future__ import annotations
import argparse
import json
import logging
import sys
import os

from data.loader import CandidateLoader
from pipeline import CortexHirePipeline
import config

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(name)s] %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cortexhire.main")

def main() -> None:
    parser = argparse.ArgumentParser(description="CortexHire — Candidate Intelligence Engine")
    parser.add_argument("--candidates", required=True,  help="Path to candidates JSON")
    parser.add_argument("--jd",         required=True,  help="Path to job description text file")
    parser.add_argument("--output",     default=config.OUTPUT_PATH)
    parser.add_argument("--top-n",      type=int, default=config.FINAL_TOP_N)
    args = parser.parse_args()

    # 1. Load Data
    loader = CandidateLoader()
    candidates = loader.load(args.candidates)
    
    with open(args.jd, 'r') as f:
        jd_text = f.read()
        
    logger.info(f"Loaded {len(candidates)} candidates")

    # 2. Run Pipeline (Observability Metrics handled internally)
    pipeline = CortexHirePipeline(jd_text=jd_text)
    result = pipeline.run(candidates)

    # 3. Save Results
    output = {
        "metadata": {
            "version": config.PIPELINE_VERSION,
            "rules_version": config.RULES_VERSION,
            "total_candidates_processed": result.metrics.total_candidates,
            "execution_time_ms": round(result.execution_time_ms, 2),
            "average_confidence": round(result.metrics.average_confidence, 2),
            "stage_latencies": {k: round(v, 2) for k, v in result.metrics.stage_latencies_ms.items()}
        },
        "top_candidates": [
            {
                "candidate_id": c.raw.candidate_id,
                "name": c.raw.name,
                "composite_score": round(c.composite_score, 2),
                "prediction_interval": round(c.prediction_interval, 2),
                "confidence_score": round(c.confidence_score, 2),
                "trust_score": round(c.trust_score, 2),
                "score_breakdown": c.score_breakdown,
                "trust_flags": [f.__dict__ for f in c.trust_flags],
                "evidence": c.evidence,
            }
            for c in result.top_candidates
        ]
    }
    
    # Ensure outputs directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Output written -> {args.output}")

if __name__ == "__main__":
    main()
