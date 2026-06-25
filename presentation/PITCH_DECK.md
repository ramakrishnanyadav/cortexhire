# CortexHire Pitch Deck Outline

## 1. The Problem (1 Slide)
* "The AI hiring market is flooded with symmetric keyword matchers."
* Show how standard systems reward "Resume Optimizers" and punish "Genuine Shippers".

## 2. Existing ATS Failure (1 Slide)
* Show a side-by-side of a terrible resume stuffed with keywords beating a sparse, metric-heavy resume of a Principal Engineer.
* "If your AI just does RAG on resumes, you are automating bad hiring."

## 3. Our Philosophy (1 Slide)
* "Most AI recruiters ask: *Who matches the job description?*"
* "CortexHire asks: *Who will actually succeed in the role?*"

## 4. Architecture: The 5 Engines (2 Slides)
* **Slide 1:** Visual flow of Eligibility -> Career Cognition -> Asymmetric Semantics -> Recruitability.
* **Slide 2:** The Trust & Uncertainty Engine. Emphasize that we model *Confidence*, not just Score. We know what we don't know.

## 5. Intelligence Engines Deep Dive (2 Slides)
* **Slide 1:** Pydantic validation, Sigmoid smoothing, and high-speed Jaccard semantic fallback. "We improve robustness against vocabulary differences while scaling within CPU constraints."
* **Slide 2:** Section-level Embeddings & Quantitative Evidence Extraction. "We don't just read 'shipped', we regex extract '10M users at 50ms latency'."

## 5.5. Alignment with Redrob Failure Modes (1 Slide)
* "CortexHire was explicitly engineered to detect the exact failure modes highlighted in the challenge:"
* Keyword stuffing (flagged by Trust Engine)
* Title-skill mismatches (flagged by Trust Engine)
* Inactive candidates (down-weighted by Behavioural Scorer)
* Sparse evidence & Confidence uncertainty (modeled natively)

## 6. Case Studies: Why Similarity Fails (3 Slides)
* *The single most important section.*
* **Slide 1 (The False Positive):** Keyword stuffer. Similarity: #1. CortexHire: #78 (Trust Penalty).
* **Slide 2 (The Hidden Gem):** Career Pivot. Similarity: #40. CortexHire: #5 (Transition Bypass).
* **Slide 3 (The Sparse Profile):** Missing dates. CortexHire outputs: `Score: 91, Confidence: 45`. "We flag for manual review instead of blindly trusting."

## 7. Evaluation & Engineering Rigor (2 Slides)
* **Slide 1:** Monte Carlo Stability Testing. Show that perturbing weights by 5% doesn't change the top 10 list.
* **Slide 2:** Ablation Study. "Removing the Trust Engine drops our Precision@10 by 20%."

## 8. Results (1 Slide)
* Show the Scatter Plot: `Composite Score vs. Confidence`.
* Point to the top-right quadrant: "Here is your next hire."

## 9. Future Work (1 Slide)
* Transitioning from heuristic confidence to Bayesian Networks for statistically true epistemic uncertainty.
* Moving from linear stages to a distributed DAG pipeline for millions of candidates.
