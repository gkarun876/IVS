"""
Sequence Miner — Length-Normalized N-gram Pattern Mining
=========================================================
Finds the most significant 2-gram and 3-gram slot-patterns across all
inscriptions, normalized by inscription length.

Why length normalization:
  A 3-gram in a 4-sign inscription accounts for 75% of that text.
  A 3-gram in a 10-sign inscription accounts for 30%.
  Raw frequency count biases toward long inscriptions.
  We weight each n-gram occurrence by 1/(inscription_length - n + 1),
  i.e., the inverse of the number of possible n-gram positions.

Two parallel analyses:
  (A) RAW SIGN N-GRAMS — most repeated actual sign sequences
      Used to identify recurring text "words" or phrases.
  (B) SLOT PATTERN N-GRAMS — patterns in INITIAL/MEDIAL/TERMINAL/AMBIGUOUS
      Used to identify grammatical templates independent of which sign fills
      each slot.

Prerequisite: syntactic_parser.py must have run first to produce:
  results/v3/slot_assignments.csv

Outputs:
  results/v3/sequence_patterns.csv   — top raw sign n-grams (length-normalized)
  results/v3/slot_patterns.csv       — top slot template patterns
  results/v3/miner_summary.txt       — annotated report
"""

import json
import csv
import os
from collections import defaultdict, Counter

CORPUS_PATH      = "data/mahadevan_corpus.json"
SLOT_ASSIGN_PATH = "results/v3/slot_assignments.csv"
RESULTS_DIR      = "results/v3"

TOP_N = 50   # how many top patterns to report


def load_corpus(path):
    with open(path) as f:
        return json.load(f)


def load_slot_assignments(path):
    """
    Returns dict: inscription_id -> list of (position, sign, slot)
    """
    assign = defaultdict(list)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assign[row["inscription_id"]].append(
                (int(row["position"]), int(row["sign"]), row["slot"])
            )
    for iid in assign:
        assign[iid].sort(key=lambda x: x[0])
    return assign


def extract_ngrams_weighted(assignments, corpus_by_id, n):
    """
    Extract n-grams weighted by 1/(length - n + 1).
    Returns two Counters:
      sign_ngram_weight  — weighted count of each (sign1, sign2[, sign3]) tuple
      slot_ngram_weight  — weighted count of each (slot1, slot2[, slot3]) tuple
    Also returns raw occurrence count for reference.
    """
    sign_weight = defaultdict(float)
    slot_weight = defaultdict(float)
    sign_raw    = Counter()
    slot_raw    = Counter()

    for iid, tokens in assignments.items():
        length = len(tokens)
        if length < n:
            continue
        n_positions = length - n + 1
        weight = 1.0 / n_positions   # normalize by possible positions

        for i in range(n_positions):
            window = tokens[i:i+n]
            sign_key = tuple(t[1] for t in window)
            slot_key = tuple(t[2] for t in window)

            sign_weight[sign_key] += weight
            slot_weight[slot_key] += weight
            sign_raw[sign_key]    += 1
            slot_raw[slot_key]    += 1

    return sign_weight, slot_weight, sign_raw, slot_raw


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    corpus      = load_corpus(CORPUS_PATH)
    corpus_by_id = {e["id"]: e for e in corpus}

    if not os.path.exists(SLOT_ASSIGN_PATH):
        print(f"ERROR: {SLOT_ASSIGN_PATH} not found.")
        print("Run syntactic_parser.py first.")
        return

    assignments = load_slot_assignments(SLOT_ASSIGN_PATH)
    print(f"Loaded slot assignments for {len(assignments)} inscriptions")

    out = []
    out.append("=" * 70)
    out.append("  SEQUENCE MINER — LENGTH-NORMALIZED N-GRAM PATTERNS")
    out.append(f"  Corpus: {len(corpus)} inscriptions, {len(assignments)} with slot data")
    out.append("=" * 70)

    # -------------------------------------------------------------------------
    # 1. Bigrams (n=2)
    # -------------------------------------------------------------------------
    s2w, sl2w, s2r, sl2r = extract_ngrams_weighted(assignments, corpus_by_id, 2)

    bigram_path = os.path.join(RESULTS_DIR, "sequence_patterns.csv")
    rows = []
    for key, wt in sorted(s2w.items(), key=lambda x: -x[1])[:TOP_N]:
        rows.append({
            "ngram_n":     2,
            "signs":       "-".join(f"M{s}" for s in key),
            "raw_count":   s2r[key],
            "weighted":    round(wt, 4),
            "type":        "sign",
        })
    for key, wt in sorted(sl2w.items(), key=lambda x: -x[1])[:TOP_N]:
        rows.append({
            "ngram_n":     2,
            "signs":       "-".join(key),
            "raw_count":   sl2r[key],
            "weighted":    round(wt, 4),
            "type":        "slot",
        })

    # -------------------------------------------------------------------------
    # 2. Trigrams (n=3)
    # -------------------------------------------------------------------------
    s3w, sl3w, s3r, sl3r = extract_ngrams_weighted(assignments, corpus_by_id, 3)

    for key, wt in sorted(s3w.items(), key=lambda x: -x[1])[:TOP_N]:
        rows.append({
            "ngram_n":     3,
            "signs":       "-".join(f"M{s}" for s in key),
            "raw_count":   s3r[key],
            "weighted":    round(wt, 4),
            "type":        "sign",
        })
    for key, wt in sorted(sl3w.items(), key=lambda x: -x[1])[:TOP_N]:
        rows.append({
            "ngram_n":     3,
            "signs":       "-".join(key),
            "raw_count":   sl3r[key],
            "weighted":    round(wt, 4),
            "type":        "slot",
        })

    with open(bigram_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ngram_n", "type", "signs", "raw_count", "weighted"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved → {bigram_path}  ({len(rows)} rows)")

    # -------------------------------------------------------------------------
    # 3. Slot template summary (the grammatically meaningful part)
    # -------------------------------------------------------------------------
    slot_path = os.path.join(RESULTS_DIR, "slot_patterns.csv")
    slot_rows = []
    for n, sw, sr in [(2, sl2w, sl2r), (3, sl3w, sl3r)]:
        for key, wt in sorted(sw.items(), key=lambda x: -x[1])[:TOP_N]:
            slot_rows.append({
                "ngram_n":   n,
                "pattern":   "-".join(key),
                "raw_count": sr[key],
                "weighted":  round(wt, 4),
            })
    with open(slot_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ngram_n", "pattern", "raw_count", "weighted"])
        writer.writeheader()
        writer.writerows(slot_rows)
    print(f"Saved → {slot_path}")

    # -------------------------------------------------------------------------
    # 4. Summary report
    # -------------------------------------------------------------------------
    out.append("")
    out.append("TOP 20 BIGRAMS BY WEIGHTED FREQUENCY (sign sequences)")
    out.append(f"  {'Signs':25s}  {'Raw':>6}  {'Weighted':>10}")
    out.append("  " + "-" * 46)
    for key, wt in sorted(s2w.items(), key=lambda x: -x[1])[:20]:
        label = "-".join(f"M{s}" for s in key)
        out.append(f"  {label:25s}  {s2r[key]:>6}  {wt:>10.4f}")

    out.append("")
    out.append("TOP 10 BIGRAM SLOT TEMPLATES")
    out.append(f"  {'Pattern':25s}  {'Raw':>6}  {'Weighted':>10}")
    out.append("  " + "-" * 46)
    for key, wt in sorted(sl2w.items(), key=lambda x: -x[1])[:10]:
        label = "-".join(key)
        out.append(f"  {label:25s}  {sl2r[key]:>6}  {wt:>10.4f}")

    out.append("")
    out.append("TOP 15 TRIGRAMS BY WEIGHTED FREQUENCY (sign sequences)")
    out.append(f"  {'Signs':35s}  {'Raw':>6}  {'Weighted':>10}")
    out.append("  " + "-" * 56)
    for key, wt in sorted(s3w.items(), key=lambda x: -x[1])[:15]:
        label = "-".join(f"M{s}" for s in key)
        out.append(f"  {label:35s}  {s3r[key]:>6}  {wt:>10.4f}")

    out.append("")
    out.append("TOP 10 TRIGRAM SLOT TEMPLATES")
    out.append(f"  {'Pattern':35s}  {'Raw':>6}  {'Weighted':>10}")
    out.append("  " + "-" * 56)
    for key, wt in sorted(sl3w.items(), key=lambda x: -x[1])[:10]:
        label = "-".join(key)
        out.append(f"  {label:35s}  {sl3r[key]:>6}  {wt:>10.4f}")

    out.append("")
    out.append("GRAMMATICAL TEMPLATE COUNTS (all slot bigrams)")
    for key, cnt in sorted(sl2r.items(), key=lambda x: -x[1])[:15]:
        label = "-".join(key)
        out.append(f"  {label:25s}  raw={cnt:>4}  weighted={sl2w[key]:.4f}")

    result = "\n".join(out)
    print("\n" + result)

    summary_path = os.path.join(RESULTS_DIR, "miner_summary.txt")
    with open(summary_path, "w") as f:
        f.write(result)
    print(f"\nSaved → {summary_path}")


if __name__ == "__main__":
    main()
