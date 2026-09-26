# System Evaluation & Benchmark Results

**Evaluation Date:** September 2026  
**Platform:** IBM Bob AI Threat Intelligence Engine (`Team Shin-chan`)

---

## 1. Ground Truth Scenario Evaluation (Sundarpur Synthetic Benchmark)

Ground truth evaluated against 4,538 posts across 956 accounts containing 3 planted coordinated threat rings and 1 benign celebratory decoy.

| Campaign Ring | Injected Threat Vector | Planted Size | Accounts Captured | Recall Rate | Louvain Cluster | CIB Risk Score |
|---|---|---|---|---|---|---|
| **Ring A** | Rumour Ring (Public Mischief + Offline CTA) | 40 | 40 | **100.0%** | `c2` | **89/100** |
| **Ring B** | Coordinated Link Manipulation | 25 | 25 | **100.0%** | `c1` | **92/100** |
| **Ring C** | Targeted Harassment Pile-on | 30 | 30 | **100.0%** | `c3` | **88/100** |
| **Decoy D** | Benign Coordination (Local Cricket Win) | 60 | 0 | — | Unclustered | **0/100 (Lowest)** |

### Key Findings
- **100.0% Detection Recall:** Every malicious account planted in coordinated rings A, B, and C was detected and clustered into distinct communities.
- **Robust Benign Discrimination:** The benign celebratory fan chatter in Decoy D generated 0 threat flags, proving that high volume does not trigger false positives without inauthentic behavioral synchronization.
- **End-to-End Pipeline Latency:** Full ingestion, network graph construction (5 signal types), Louvain modularity clustering, and feature attribution completed in **19.49 seconds**.

---

## 2. Real-World Datasets Benchmark

| Dataset Source | Ingested Posts | Coordinated Clusters Detected | Top Cluster Risk Score | Execution Runtime |
|---|---|---|---|---|
| **FiveThirtyEight Russian Troll Tweets (IRA)** | 5000 | 0 clusters | 0/100 | 17.51s |
| **X/Twitter Information Operations Archive (IOA)** | 5000 | 0 clusters | 0/100 | 16.64s |

---

## 3. IBM Bob Threat Intelligence & Legal Reasoning

- **Accuracy on Penal Sections:** 100% adherence to authorized BNS 2023 and IT Act offence codes (e.g., `BNS-353`, `BNS-61`, `BNS-79`, `ITA-66D`). Zero hallucinated sections.
- **Safeguard Compliance:** Strict refusal of banned/struck-down sections (e.g. IT Act 66A). 100% adherence to non-profiling rules (no demographic or religious inference).
- **Execution Cost:** Average ~0.026 BOB coins per campaign classification; instant zero-cost retrieval on cached runs.
