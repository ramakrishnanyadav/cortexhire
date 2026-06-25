# evaluation/visualize.py
from __future__ import annotations
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortexhire.visualize")

def plot_score_vs_confidence(results_json_path: str):
    """
    Simulates generating a scatter plot of Composite Score vs Confidence.
    In a real system, this would use matplotlib/seaborn.
    """
    logger.info("--- CortexHire Visualization ---")
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        with open(results_json_path, 'r') as f:
            data = json.load(f)
            
        scores = []
        confidences = []
        labels = []
        
        for c in data.get("top_candidates", []):
            scores.append(c["composite_score"])
            confidences.append(c["confidence_score"])
            labels.append(c["name"])
            
        if not scores:
            logger.warning("No candidates found in output to plot.")
            return
            
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=confidences, y=scores, s=100)
        
        for i, txt in enumerate(labels):
            plt.annotate(txt, (confidences[i], scores[i]), xytext=(5,5), textcoords='offset points')
            
        plt.title("Candidate Quality: Composite Score vs Confidence")
        plt.xlabel("Confidence Score (Reliability of Evidence)")
        plt.ylabel("Composite Score (Overall Fit)")
        plt.axvline(x=70, color='r', linestyle='--', alpha=0.5, label='High Confidence Threshold')
        plt.axhline(y=70, color='g', linestyle='--', alpha=0.5, label='High Quality Threshold')
        plt.legend()
        
        # Save plot
        output_path = "outputs/score_vs_confidence.png"
        import os
        os.makedirs("outputs", exist_ok=True)
        plt.savefig(output_path)
        logger.info(f"Plot saved to {output_path}")
        
    except ImportError:
        logger.warning("matplotlib or seaborn not installed. Please install them to generate the plot.")
        logger.info("Plotting logic is implemented and ready.")
    except Exception:
        logger.exception("Error generating plot:")

if __name__ == "__main__":
    plot_score_vs_confidence("outputs/final_ranking.json")
