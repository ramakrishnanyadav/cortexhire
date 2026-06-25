# evaluation/profiler.py
from __future__ import annotations
import cProfile
import pstats
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortexhire.profiler")

def run_profiler(main_func):
    """
    Runs the pipeline under cProfile to verify O(n) claims and locate bottlenecks.
    """
    logger.info("--- CortexHire Execution Profiler ---")
    pr = cProfile.Profile()
    pr.enable()
    
    main_func()
    
    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(20) # Top 20 time sinks
    
    logger.info("Profiler Top 20 Cumulative Time Sinks:")
    logger.info("\n" + s.getvalue())
