# evaluation/stability.py
from __future__ import annotations
import copy
import random
import logging
import math
from ranking.ranker import CompositeRanker
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortexhire.stability")

def run_monte_carlo_stability(candidates, iterations=1000, perturbation_pct=0.05):
    """
    Monte Carlo simulation to verify ranking stability under weight perturbations.
    """
    logger.info(f"--- CortexHire Monte Carlo Ranking Stability ({iterations} iterations) ---")
    
    # Store original weights
    orig_weights = {
        "ELIGIBILITY": config.WEIGHT_ELIGIBILITY,
        "CAREER": config.WEIGHT_CAREER,
        "SEMANTIC": config.WEIGHT_SEMANTIC_MATCH,
        "RECRUITABILITY": config.WEIGHT_RECRUITABILITY,
        "TRUST": config.WEIGHT_TRUST
    }
    
    appearances = {c.raw.candidate_id: 0 for c in candidates}
    
    ranker = CompositeRanker()
    
    for _ in range(iterations):
        # Perturb weights by +/- perturbation_pct
        w_eligibility = orig_weights["ELIGIBILITY"] * (1.0 + random.uniform(-perturbation_pct, perturbation_pct))
        w_career = orig_weights["CAREER"] * (1.0 + random.uniform(-perturbation_pct, perturbation_pct))
        w_semantic = orig_weights["SEMANTIC"] * (1.0 + random.uniform(-perturbation_pct, perturbation_pct))
        w_recruitability = orig_weights["RECRUITABILITY"] * (1.0 + random.uniform(-perturbation_pct, perturbation_pct))
        w_trust = orig_weights["TRUST"] * (1.0 + random.uniform(-perturbation_pct, perturbation_pct))
        
        # Normalize back to 1.0
        total = w_eligibility + w_career + w_semantic + w_recruitability + w_trust
        
        # Temporarily patch config
        config.WEIGHT_ELIGIBILITY = w_eligibility / total
        config.WEIGHT_CAREER = w_career / total
        config.WEIGHT_SEMANTIC_MATCH = w_semantic / total
        config.WEIGHT_RECRUITABILITY = w_recruitability / total
        config.WEIGHT_TRUST = w_trust / total
        
        top_n = ranker.rank(copy.deepcopy(candidates))
        
        for c in top_n:
            appearances[c.raw.candidate_id] += 1
            
    # Restore config
    config.WEIGHT_ELIGIBILITY = orig_weights["ELIGIBILITY"]
    config.WEIGHT_CAREER = orig_weights["CAREER"]
    config.WEIGHT_SEMANTIC_MATCH = orig_weights["SEMANTIC"]
    config.WEIGHT_RECRUITABILITY = orig_weights["RECRUITABILITY"]
    config.WEIGHT_TRUST = orig_weights["TRUST"]
    
    logger.info("Stability Results (Frequency in Top N across perturbed weights):")
    for cid, count in sorted(appearances.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / iterations) * 100
        status = "Stable" if percentage > 90.0 else "Unstable"
        logger.info(f"Candidate {cid}: {percentage:.1f}% ({status})")
