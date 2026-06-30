"""
Full-corpus proof runner — Mahadevan sign integers
===================================================
Runs all 4 proofs on the 2,742-inscription clean corpus.
Terminal sign: 342 (Mahadevan jar sign).
Output saved to results/v2/proof_results.txt
"""

import json
import math
import os
from collections import Counter, defaultdict
from scipy import stats

CORPUS_PATH  = "data/mahadevan_corpus.json"
RESULTS_DIR  = "results/v2"
RESULTS_FILE = os.path.join(RESULTS_DIR, "proof_results.txt")

TERMINAL = 342   # Mahadevan sign 342 — confirmed terminal marker


def load_corpus(path: str) -> list[list[int]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [e["seq"] for e in data]


# ---------------------------------------------------------------------------
# Proof 1 — Suffix Theorem
# H0: P(342 is terminal | 342 appears) = uniform across positions
# ---------------------------------------------------------------------------
def proof1(seqs):
    terminal_count = 0
    total_occ      = 0

    for seq in seqs:
        for i, s in enumerate(seq):
            if s == TERMINAL:
                total_occ += 1
                if i == len(seq) - 1:
                    terminal_count += 1

    if total_occ == 0:
        return {"error": "sign 342 not found"}

    # null probability: if uniform, terminal position prob = 1/avg_length
    avg_len  = sum(len(s) for s in seqs) / len(seqs)
    null_p   = 1.0 / avg_len
    p_value  = stats.binomtest(terminal_count, total_occ, null_p, alternative="greater").pvalue
    rate     = terminal_count / total_occ

    return {
        "occurrences":     total_occ,
        "terminal_count":  terminal_count,
        "terminal_rate":   rate,
        "null_prob":       null_p,
        "p_value":         p_value,
        "verdict":         "H0 REJECTED" if p_value < 0.05 else "H0 NOT REJECTED",
    }


# ---------------------------------------------------------------------------
# Proof 2 — Positional Entropy
# Entropy at position 0 vs position 1 (drop in entropy = structure)
# ---------------------------------------------------------------------------
def proof2(seqs):
    pos_signs = defaultdict(list)
    for seq in seqs:
        for i, s in enumerate(seq):
            pos_signs[i].append(s)

    def entropy(signs):
        c = Counter(signs)
        n = len(signs)
        return -sum((v/n) * math.log2(v/n) for v in c.values())

    h0 = entropy(pos_signs[0])
    h1 = entropy(pos_signs[1]) if pos_signs[1] else 0
    drop = h0 - h1

    return {
        "entropy_pos0": round(h0, 3),
        "entropy_pos1": round(h1, 3),
        "entropy_drop": round(drop, 3),
        "verdict": "STRUCTURE_CONFIRMED" if drop >= 0.3 else "INCONCLUSIVE",
    }


# ---------------------------------------------------------------------------
# Proof 3 — Co-occurrence Cluster Chi-square
# Signs 267, 99, 342 hypothesised to cluster
# ---------------------------------------------------------------------------
def proof3(seqs):
    cluster = {267, 99, 342}
    co_count = 0
    for seq in seqs:
        present = set(seq)
        if cluster.issubset(present):
            co_count += 1

    n      = len(seqs)
    freqs  = {s: sum(1 for seq in seqs if s in seq) / n for s in cluster}
    expected = n
    for f in freqs.values():
        expected *= f

    if expected == 0:
        return {"error": "expected = 0"}

    chi2   = (co_count - expected) ** 2 / expected
    p_val  = 1 - stats.chi2.cdf(chi2, df=1)

    return {
        "cluster":    list(cluster),
        "observed":   co_count,
        "expected":   round(expected, 2),
        "chi2":       round(chi2, 4),
        "p_value":    round(p_val, 6),
        "verdict":    "CLUSTER_CONFIRMED" if p_val < 0.05 else "NOT_SIGNIFICANT",
    }


# ---------------------------------------------------------------------------
# Proof 4 — Agglutination Ratio
# Bigram (preceding_sign → 342) observed vs expected
# ---------------------------------------------------------------------------
def proof4(seqs):
    bigrams  = Counter()
    unigrams = Counter()

    for seq in seqs:
        unigrams.update(seq)
        for i in range(len(seq) - 1):
            bigrams[(seq[i], seq[i+1])] += 1

    total_bigrams = sum(bigrams.values())
    total_signs   = sum(unigrams.values())

    # top predecessor of 342
    preds = {a: cnt for (a, b), cnt in bigrams.items() if b == TERMINAL}
    if not preds:
        return {"error": "no bigrams ending in 342"}

    top_pred, top_count = max(preds.items(), key=lambda x: x[1])

    p_top  = unigrams[top_pred] / total_signs
    p_term = unigrams[TERMINAL] / total_signs
    expected = p_top * p_term * total_bigrams
    ratio  = top_count / expected if expected > 0 else 0

    return {
        "top_predecessor": top_pred,
        "observed":        top_count,
        "expected":        round(expected, 2),
        "ratio":           round(ratio, 2),
        "verdict":         "AGGLUTINATION_CONFIRMED" if ratio >= 3 else "WEAK",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    seqs = load_corpus(CORPUS_PATH)

    lines = []
    lines.append("=" * 62)
    lines.append("  INDUS VALLEY SCRIPT — FULL CORPUS PROOFS (v2.0)")
    lines.append(f"  Corpus: {len(seqs)} clean inscriptions (Mahadevan)")
    lines.append(f"  Terminal sign: M{TERMINAL}")
    lines.append("=" * 62)

    lines.append("\nPROOF 1 — Suffix Theorem")
    r = proof1(seqs)
    for k, v in r.items():
        lines.append(f"  {k:<20} {v}")

    lines.append("\nPROOF 2 — Positional Entropy")
    r = proof2(seqs)
    for k, v in r.items():
        lines.append(f"  {k:<20} {v}")

    lines.append("\nPROOF 3 — Co-occurrence Cluster")
    r = proof3(seqs)
    for k, v in r.items():
        lines.append(f"  {k:<20} {v}")

    lines.append("\nPROOF 4 — Agglutination Ratio")
    r = proof4(seqs)
    for k, v in r.items():
        lines.append(f"  {k:<20} {v}")

    lines.append("")
    output = "\n".join(lines)
    print(output)

    with open(RESULTS_FILE, "w") as f:
        f.write(output)
    print(f"\nSaved → {RESULTS_FILE}")


if __name__ == "__main__":
    main()
