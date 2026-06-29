"""
Grammar Engine — Markov bigram transition matrix
=================================================
Builds a full bigram transition matrix from the clean Mahadevan corpus.
No linguistic assumptions. Reports what the data shows, nothing else.

Outputs:
    results/v2/transition_matrix.csv   — P(j|i) for all sign pairs with >= MIN_OCC
    results/v2/top_transitions.txt     — top 30 highest-probability transitions
    results/v2/positional_profile.csv  — for each sign: prefix_rate, suffix_rate, medial_rate
    results/v2/grammar_summary.txt     — structural observations (data only, no interpretation)
"""

import json
import csv
import os
import math
from collections import Counter, defaultdict

CORPUS_PATH = "data/mahadevan_corpus.json"
RESULTS_DIR = "results/v2"
MIN_OCC     = 3   # minimum co-occurrences to include in matrix

TERMINAL = 342


def load_seqs(path):
    with open(path) as f:
        data = json.load(f)
    return [e["seq"] for e in data], [e["site"] for e in data]


def build_bigram_matrix(seqs):
    """
    Returns:
        unigram: Counter of sign frequencies
        bigram:  Counter of (a, b) pair frequencies
        cond:    dict[(a,b)] = P(b|a)
    """
    unigram = Counter()
    bigram  = Counter()

    for seq in seqs:
        unigram.update(seq)
        for i in range(len(seq) - 1):
            bigram[(seq[i], seq[i+1])] += 1

    # conditional probability P(b|a) = count(a,b) / count(a as non-final)
    # denominator = number of times sign a appears NOT in last position
    non_final = Counter()
    for seq in seqs:
        for s in seq[:-1]:
            non_final[s] += 1

    cond = {}
    for (a, b), cnt in bigram.items():
        if cnt >= MIN_OCC and non_final[a] > 0:
            cond[(a, b)] = cnt / non_final[a]

    return unigram, bigram, cond, non_final


def positional_profile(seqs, unigram):
    """
    For each sign compute:
        initial_rate  = P(sign at position 0)
        terminal_rate = P(sign at last position)
        medial_rate   = 1 - initial - terminal
    Rates are relative to total occurrences of that sign.
    """
    initial  = Counter()
    terminal = Counter()
    total    = Counter()

    for seq in seqs:
        total.update(seq)
        initial[seq[0]]  += 1
        terminal[seq[-1]] += 1

    profile = {}
    for sign, cnt in total.items():
        i_rate = initial[sign]  / cnt
        t_rate = terminal[sign] / cnt
        m_rate = max(0.0, 1.0 - i_rate - t_rate)
        profile[sign] = {
            "count":         cnt,
            "initial_rate":  round(i_rate, 4),
            "terminal_rate": round(t_rate, 4),
            "medial_rate":   round(m_rate, 4),
        }

    return profile


def entropy(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum((v/n) * math.log2(v/n) for v in counter.values() if v > 0)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    seqs, sites = load_seqs(CORPUS_PATH)
    print(f"Corpus: {len(seqs)} inscriptions")

    unigram, bigram, cond, non_final = build_bigram_matrix(seqs)
    profile = positional_profile(seqs, unigram)

    # -----------------------------------------------------------------------
    # 1. Save transition matrix CSV
    # -----------------------------------------------------------------------
    matrix_path = os.path.join(RESULTS_DIR, "transition_matrix.csv")
    with open(matrix_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["from_sign", "to_sign", "count", "P(to|from)"])
        for (a, b), p in sorted(cond.items(), key=lambda x: -x[1]):
            writer.writerow([a, b, bigram[(a,b)], round(p, 6)])
    print(f"Saved → {matrix_path}  ({len(cond)} transitions)")

    # -----------------------------------------------------------------------
    # 2. Top 30 transitions
    # -----------------------------------------------------------------------
    top_path = os.path.join(RESULTS_DIR, "top_transitions.txt")
    top30 = sorted(cond.items(), key=lambda x: -x[1])[:30]
    lines = ["TOP 30 BIGRAM TRANSITIONS  P(B|A) — no linguistic labels\n",
             f"{'A':>6}  {'B':>6}  {'count':>6}  {'P(B|A)':>8}  {'obs/exp':>8}\n",
             "-" * 48]
    total_bigrams = sum(bigram.values())
    total_signs   = sum(unigram.values())
    for (a, b), p in top30:
        cnt      = bigram[(a, b)]
        p_a      = non_final[a] / total_bigrams if total_bigrams else 0
        p_b      = unigram[b]   / total_signs   if total_signs   else 0
        expected = p_a * p_b * total_bigrams
        ratio    = cnt / expected if expected > 0 else 0
        lines.append(f"{a:>6}  {b:>6}  {cnt:>6}  {p:>8.4f}  {ratio:>8.2f}x")
    with open(top_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Saved → {top_path}")

    # -----------------------------------------------------------------------
    # 3. Positional profile CSV
    # -----------------------------------------------------------------------
    prof_path = os.path.join(RESULTS_DIR, "positional_profile.csv")
    with open(prof_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sign", "count", "initial_rate", "terminal_rate", "medial_rate"])
        for sign, p in sorted(profile.items(), key=lambda x: -x[1]["count"]):
            writer.writerow([sign, p["count"], p["initial_rate"],
                             p["terminal_rate"], p["medial_rate"]])
    print(f"Saved → {prof_path}  ({len(profile)} signs)")

    # -----------------------------------------------------------------------
    # 4. Grammar summary — data only, no interpretation
    # -----------------------------------------------------------------------
    # Signs with >70% terminal rate (candidate suffixes)
    high_terminal = [(s, p) for s, p in profile.items()
                     if p["terminal_rate"] >= 0.70 and p["count"] >= 10]
    high_terminal.sort(key=lambda x: -x[1]["terminal_rate"])

    # Signs with >70% initial rate (candidate prefixes)
    high_initial = [(s, p) for s, p in profile.items()
                    if p["initial_rate"] >= 0.70 and p["count"] >= 10]
    high_initial.sort(key=lambda x: -x[1]["initial_rate"])

    # Signs with >80% medial rate (candidate roots/medials)
    high_medial = [(s, p) for s, p in profile.items()
                   if p["medial_rate"] >= 0.80 and p["count"] >= 10]
    high_medial.sort(key=lambda x: -x[1]["medial_rate"])

    # Positional entropy per slot
    pos_counters = defaultdict(Counter)
    for seq in seqs:
        for i, s in enumerate(seq):
            pos_counters[i][s] += 1
    pos_entropy = {i: round(entropy(c), 3) for i, c in pos_counters.items() if len(c) > 1}

    # Average inscription length
    lengths = [len(s) for s in seqs]
    avg_len = sum(lengths) / len(lengths)
    max_len = max(lengths)

    summary_path = os.path.join(RESULTS_DIR, "grammar_summary.txt")
    out = []
    out.append("=" * 62)
    out.append("  GRAMMAR ENGINE SUMMARY — DATA ONLY")
    out.append(f"  Corpus: {len(seqs)} inscriptions, {sum(unigram.values())} total sign tokens")
    out.append(f"  Unique signs: {len(unigram)}")
    out.append(f"  Avg length: {avg_len:.2f}  Max: {max_len}")
    out.append("=" * 62)

    out.append(f"\nPOSITIONAL ENTROPY (bits) — slot 0 = leftmost in array")
    for i in sorted(pos_entropy)[:8]:
        out.append(f"  Position {i}: {pos_entropy[i]} bits")

    out.append(f"\nSIGNS WITH terminal_rate >= 70%  (count >= 10)")
    out.append(f"  {'sign':>6}  {'count':>6}  {'term%':>7}  {'init%':>7}  {'medi%':>7}")
    for s, p in high_terminal[:15]:
        out.append(f"  {s:>6}  {p['count']:>6}  {p['terminal_rate']*100:>6.1f}%"
                   f"  {p['initial_rate']*100:>6.1f}%  {p['medial_rate']*100:>6.1f}%")

    out.append(f"\nSIGNS WITH initial_rate >= 70%  (count >= 10)")
    out.append(f"  {'sign':>6}  {'count':>6}  {'init%':>7}  {'term%':>7}  {'medi%':>7}")
    for s, p in high_initial[:15]:
        out.append(f"  {s:>6}  {p['count']:>6}  {p['initial_rate']*100:>6.1f}%"
                   f"  {p['terminal_rate']*100:>6.1f}%  {p['medial_rate']*100:>6.1f}%")

    out.append(f"\nSIGNS WITH medial_rate >= 80%  (count >= 10)")
    out.append(f"  {'sign':>6}  {'count':>6}  {'medi%':>7}  {'init%':>7}  {'term%':>7}")
    for s, p in high_medial[:15]:
        out.append(f"  {s:>6}  {p['count']:>6}  {p['medial_rate']*100:>6.1f}%"
                   f"  {p['initial_rate']*100:>6.1f}%  {p['terminal_rate']*100:>6.1f}%")

    out.append(f"\nTOP 10 MOST FREQUENT SIGNS")
    for s, cnt in unigram.most_common(10):
        p = profile[s]
        out.append(f"  M{s:<5} freq={cnt:<5}  "
                   f"init={p['initial_rate']*100:.1f}%  "
                   f"term={p['terminal_rate']*100:.1f}%  "
                   f"medi={p['medial_rate']*100:.1f}%")

    out.append("")
    result = "\n".join(out)
    print("\n" + result)

    with open(summary_path, "w") as f:
        f.write(result)
    print(f"Saved → {summary_path}")


if __name__ == "__main__":
    main()
