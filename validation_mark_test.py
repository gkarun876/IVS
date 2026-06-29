"""
Cross-Site Markov Consistency Test
====================================
Trains a bigram transition matrix on Mohenjo-daro inscriptions only,
then scores Harappa inscriptions against it using log-likelihood.
Compares real Harappa score vs 1000 random-shuffle baseline scores.

If real Harappa log-likelihood >> random baseline:
    The script follows the same grammar across 500+ miles → unified system.

No linguistic assumptions. Reports what the data shows.

Output: results/v2/cross_site_consistency.txt
"""

import json
import math
import random
import os
from collections import Counter, defaultdict
from scipy import stats

CORPUS_PATH = "data/mahadevan_corpus.json"
RESULTS_DIR = "results/v2"
OUT_FILE    = os.path.join(RESULTS_DIR, "cross_site_consistency.txt")

SMOOTHING   = 1e-6   # Laplace-like floor for unseen transitions
N_SHUFFLES  = 1000
RANDOM_SEED = 42


def load_corpus(path):
    with open(path) as f:
        data = json.load(f)
    return data


def build_matrix(seqs):
    """
    Build bigram transition probabilities from a list of sign sequences.
    Returns dict: (a, b) -> P(b|a)
    Also returns unigram counts for smoothing denominator.
    """
    bigram   = Counter()
    non_final = Counter()

    for seq in seqs:
        for i in range(len(seq) - 1):
            bigram[(seq[i], seq[i+1])] += 1
            non_final[seq[i]] += 1

    # All unique signs seen
    all_signs = set()
    for seq in seqs:
        all_signs.update(seq)

    matrix = {}
    for a in all_signs:
        denom = non_final[a] + SMOOTHING * len(all_signs)
        for b in all_signs:
            matrix[(a, b)] = (bigram[(a, b)] + SMOOTHING) / denom

    return matrix, all_signs


def score_corpus(seqs, matrix, all_signs):
    """
    Compute mean log-likelihood per bigram for a set of sequences
    against the given transition matrix.
    Higher (less negative) = better fit to the grammar.
    """
    log_sum = 0.0
    count   = 0

    for seq in seqs:
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i+1]
            p = matrix.get((a, b), SMOOTHING)
            log_sum += math.log(p)
            count   += 1

    return log_sum / count if count > 0 else float("-inf")


def shuffle_seqs(seqs, rng):
    """Randomly permute signs within each inscription (destroys order, preserves sign pool)."""
    shuffled = []
    for seq in seqs:
        s = seq[:]
        rng.shuffle(s)
        shuffled.append(s)
    return shuffled


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    data = load_corpus(CORPUS_PATH)

    # Split by site
    by_site = defaultdict(list)
    for entry in data:
        by_site[entry["site"]].append(entry["seq"])

    sites_available = {site: len(seqs) for site, seqs in by_site.items()}

    md_seqs = by_site["Mohenjo-daro"]
    hp_seqs = by_site["Harappa"]

    lines = []
    lines.append("=" * 62)
    lines.append("  CROSS-SITE MARKOV CONSISTENCY TEST")
    lines.append("  Train: Mohenjo-daro | Test: Harappa")
    lines.append("=" * 62)
    lines.append("")
    lines.append("Corpus split:")
    for site, cnt in sorted(sites_available.items(), key=lambda x: -x[1]):
        lines.append(f"  {site:<22} {cnt} inscriptions")

    lines.append(f"\nTraining matrix on {len(md_seqs)} Mohenjo-daro inscriptions...")
    matrix, all_signs = build_matrix(md_seqs)
    lines.append(f"Matrix built: {len(all_signs)} unique signs, "
                 f"{len([k for k in matrix if matrix[k] > SMOOTHING*2])} non-trivial transitions")

    # Score real Harappa data
    real_score = score_corpus(hp_seqs, matrix, all_signs)
    lines.append(f"\nReal Harappa log-likelihood/bigram:  {real_score:.4f}")

    # Score Mohenjo-daro on itself (upper bound reference)
    md_self_score = score_corpus(md_seqs, matrix, all_signs)
    lines.append(f"MD self-score (upper bound ref):     {md_self_score:.4f}")

    # Random shuffle baseline
    lines.append(f"\nGenerating {N_SHUFFLES} random-shuffle baselines...")
    rng = random.Random(RANDOM_SEED)
    shuffle_scores = []
    for _ in range(N_SHUFFLES):
        shuffled = shuffle_seqs(hp_seqs, rng)
        shuffle_scores.append(score_corpus(shuffled, matrix, all_signs))

    baseline_mean = sum(shuffle_scores) / len(shuffle_scores)
    baseline_std  = (sum((s - baseline_mean)**2 for s in shuffle_scores) / len(shuffle_scores)) ** 0.5

    lines.append(f"Random baseline mean:                {baseline_mean:.4f}")
    lines.append(f"Random baseline std:                 {baseline_std:.4f}")

    # Z-score and t-test
    z_score = (real_score - baseline_mean) / baseline_std if baseline_std > 0 else 0
    t_stat, p_value = stats.ttest_1samp(shuffle_scores, real_score)
    p_value = p_value / 2  # one-tailed: real > baseline

    lines.append(f"\nZ-score (real vs random):            {z_score:.2f}")
    lines.append(f"p-value (one-tailed t-test):         {p_value:.2e}")

    # Verdict
    lines.append("")
    lines.append("-" * 62)
    if z_score > 3 and p_value < 0.05:
        verdict = ("UNIFIED_SYSTEM_CONFIRMED: Harappa inscriptions fit the "
                   "Mohenjo-daro grammar significantly better than random. "
                   "The script follows consistent structural rules across sites.")
    elif z_score > 1.5:
        verdict = ("PARTIAL_CONSISTENCY: Harappa fits MD grammar better than "
                   "random but below 3-sigma threshold. Inconclusive.")
    else:
        verdict = ("NO_CONSISTENCY: Harappa does not fit MD grammar better "
                   "than random. Sites may use independent symbol systems.")

    lines.append(f"VERDICT: {verdict}")
    lines.append("-" * 62)

    # Per-site scores (additional sites scored against MD matrix)
    lines.append("\nALL SITES scored against Mohenjo-daro matrix:")
    lines.append(f"  {'Site':<22} {'N':>5}  {'LL/bigram':>10}  {'vs random':>10}")
    for site, seqs in sorted(by_site.items(), key=lambda x: -len(x[1])):
        if len(seqs) < 10:
            continue
        sc = score_corpus(seqs, matrix, all_signs)
        diff = sc - baseline_mean
        lines.append(f"  {site:<22} {len(seqs):>5}  {sc:>10.4f}  {diff:>+10.4f}")

    output = "\n".join(lines)
    print(output)

    with open(OUT_FILE, "w") as f:
        f.write(output)
    print(f"\nSaved → {OUT_FILE}")


if __name__ == "__main__":
    main()
