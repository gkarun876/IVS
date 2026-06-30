"""
Motif Correlation Analysis
==========================
Tests whether high-PMI sign pairs (from mi_network.py) cluster on specific
motif types (fs80) more than chance predicts.

Primary target: M172-M304 (PMI=7.9, strongest pair in network)
Secondary: top 20 PMI pairs from results/v4/mi_edges.csv

Data:
  data/mahadevan_corpus.json  — sign sequences with textnum
  data/motif_data.json        — fs80, dir, inscobj per textnum
  data/codebook.py            — fs80 → motif label

Output:
  results/v4/motif_correlation.csv   — per sign-pair: motif distribution + chi-square
  results/v4/motif_summary.txt       — human-readable findings
"""

import json
import csv
import os
import math
from collections import Counter, defaultdict
from scipy.stats import chi2_contingency

sys_import = __import__("sys")
sys_import.path.insert(0, "data")
from codebook import fs80_label, inscobj_label, dir_label, site_from_textnum

CORPUS_PATH   = "data/mahadevan_corpus.json"
MOTIF_PATH    = "data/motif_data.json"
MI_EDGES_PATH = "results/v4/mi_edges.csv"
RESULTS_DIR   = "results/v4"

TOP_N_PAIRS   = 20   # test top N PMI pairs
MIN_COOC      = 3    # minimum co-occurrences to test a pair


def load_corpus(path):
    with open(path) as f:
        data = json.load(f)
    return data   # list of {id, site, seq, textnum}


def load_motif(path):
    with open(path) as f:
        data = json.load(f)
    # key by textnum; prefer sideline=0 (only side) else first record
    motif_map = {}
    for rec in data:
        tn = rec["textnum"]
        if tn not in motif_map or str(rec.get("sideline", "")) == "0":
            motif_map[tn] = rec
    return motif_map


def load_mi_edges(path, top_n):
    pairs = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append((int(row["sign_a"]), int(row["sign_b"]),
                          float(row["pmi_score"]), int(row["co_occurrence_count"])))
    pairs.sort(key=lambda x: -x[2])
    return pairs[:top_n]


def get_textnums_with_pair(corpus, sign_a, sign_b):
    """Return list of textnums where both sign_a and sign_b appear in seq."""
    result = []
    for entry in corpus:
        seq = entry.get("seq", [])
        if sign_a in seq and sign_b in seq:
            tn = entry.get("textnum")
            if tn:
                result.append(tn)
    return result


def get_textnums_without_pair(corpus, sign_a, sign_b, with_textnums):
    """Return textnums that have neither sign — background baseline."""
    with_set = set(with_textnums)
    result = []
    for entry in corpus:
        tn = entry.get("textnum")
        if tn and tn not in with_set:
            result.append(tn)
    return result


def motif_distribution(textnums, motif_map):
    """Count fs80 label occurrences for a list of textnums."""
    counts = Counter()
    for tn in textnums:
        rec = motif_map.get(tn)
        if rec:
            fs = rec.get("fs80", 0) or 0
            counts[fs80_label(fs)] += 1
        else:
            counts["NO-DATA"] += 1
    return counts


def chi_square_test(pair_dist, base_dist, label):
    """
    Chi-square test: does pair_dist differ from base_dist in motif proportions?
    Only includes categories present in pair_dist with count >= 2.
    Returns chi2, p, degrees of freedom.
    """
    categories = [k for k, v in pair_dist.items() if v >= 2 and k != "NO-DATA"]
    if len(categories) < 2:
        return None, None, None

    pair_total = sum(pair_dist.values())
    base_total = sum(base_dist.values())
    if base_total == 0:
        return None, None, None

    observed = []
    expected = []
    for cat in categories:
        obs = pair_dist.get(cat, 0)
        base_rate = base_dist.get(cat, 0) / base_total
        exp = base_rate * pair_total
        if exp > 0:
            observed.append(obs)
            expected.append(exp)

    if len(observed) < 2:
        return None, None, None

    # Manual chi-square
    chi2 = sum((o - e) ** 2 / e for o, e in zip(observed, expected))
    df   = len(observed) - 1
    # approximate p from chi2 table (use scipy)
    from scipy.stats import chi2 as chi2_dist
    p = 1 - chi2_dist.cdf(chi2, df)
    return chi2, p, df


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    corpus   = load_corpus(CORPUS_PATH)
    motif_map = load_motif(MOTIF_PATH)
    print(f"Corpus: {len(corpus)} inscriptions")
    print(f"Motif map: {len(motif_map)} textnums")

    # check textnum coverage
    # corpus uses 'id' field as textnum (string), motif_map keys are ints
    for e in corpus:
        if "textnum" not in e:
            try:
                e["textnum"] = int(str(e.get("id", "")).rstrip("ab").split("-")[0])
            except Exception:
                pass
    corpus_tns = set(e.get("textnum") for e in corpus if e.get("textnum"))
    motif_tns  = set(motif_map.keys())
    overlap    = corpus_tns & motif_tns
    print(f"Textnum overlap: {len(overlap)} of {len(corpus_tns)} corpus inscriptions have motif data")

    # Load top PMI pairs
    if not os.path.exists(MI_EDGES_PATH):
        print(f"ERROR: {MI_EDGES_PATH} not found. Run mi_network.py first.")
        return

    pairs = load_mi_edges(MI_EDGES_PATH, TOP_N_PAIRS)
    print(f"Testing top {len(pairs)} PMI pairs")

    # Background motif distribution (all inscriptions)
    all_textnums = [e.get("textnum") for e in corpus if e.get("textnum")]
    base_dist    = motif_distribution(all_textnums, motif_map)
    base_total   = sum(v for k, v in base_dist.items() if k != "NO-DATA")
    print(f"\nBackground motif distribution (top 5):")
    for label, cnt in base_dist.most_common(5):
        print(f"  {label:25s} {cnt:4d}  ({cnt/base_total*100:.1f}%)")

    # Per-pair analysis
    results = []
    for sign_a, sign_b, pmi, cooc in pairs:
        with_tns    = get_textnums_with_pair(corpus, sign_a, sign_b)
        pair_dist   = motif_distribution(with_tns, motif_map)
        chi2, p, df = chi_square_test(pair_dist, base_dist, f"M{sign_a}-M{sign_b}")

        pair_total  = sum(v for k, v in pair_dist.items() if k != "NO-DATA")
        top_motif   = pair_dist.most_common(1)[0] if pair_dist else ("NONE", 0)
        top_rate    = top_motif[1] / pair_total if pair_total > 0 else 0
        base_rate   = base_dist.get(top_motif[0], 0) / base_total if base_total > 0 else 0
        enrichment  = top_rate / base_rate if base_rate > 0 else 0

        results.append({
            "sign_a":       sign_a,
            "sign_b":       sign_b,
            "pmi":          round(pmi, 3),
            "cooc":         cooc,
            "n_with_pair":  len(with_tns),
            "top_motif":    top_motif[0],
            "top_motif_n":  top_motif[1],
            "top_motif_%":  round(top_rate * 100, 1),
            "base_%":       round(base_rate * 100, 1),
            "enrichment_x": round(enrichment, 2),
            "chi2":         round(chi2, 3) if chi2 else "n/a",
            "p_value":      f"{p:.4f}" if p else "n/a",
            "df":           df if df else "n/a",
        })

    # Save CSV
    csv_path = os.path.join(RESULTS_DIR, "motif_correlation.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved → {csv_path}")

    # Summary text
    out = []
    out.append("=" * 70)
    out.append("  MOTIF CORRELATION ANALYSIS")
    out.append(f"  Corpus: {len(corpus)} inscriptions | Motif data: {len(motif_map)} textnums")
    out.append(f"  Overlap: {len(overlap)} inscriptions have both sign seq + motif")
    out.append("=" * 70)

    out.append(f"\nBACKGROUND MOTIF DISTRIBUTION (all {base_total} inscriptions with motif data)")
    for label, cnt in base_dist.most_common(8):
        if label == "NO-DATA":
            continue
        out.append(f"  {label:30s} {cnt:4d}  ({cnt/base_total*100:.1f}%)")

    out.append(f"\nTOP {len(results)} PMI PAIRS — MOTIF ENRICHMENT")
    out.append(f"  {'Pair':12s} {'PMI':>6} {'N':>5} {'Top Motif':30s} {'Pair%':>6} {'Base%':>6} {'Enrich':>7} {'p':>8}")
    out.append("  " + "-" * 85)
    for r in sorted(results, key=lambda x: -(x["enrichment_x"] if isinstance(x["enrichment_x"], float) else 0)):
        out.append(
            f"  M{r['sign_a']}-M{r['sign_b']:5} "
            f"{r['pmi']:>6.2f} "
            f"{r['n_with_pair']:>5} "
            f"{r['top_motif']:30s} "
            f"{r['top_motif_%']:>5.1f}% "
            f"{r['base_%']:>5.1f}% "
            f"{r['enrichment_x']:>6.1f}x "
            f"{str(r['p_value']):>8}"
        )

    # Highlight M172-M304 specifically
    target = next((r for r in results if
                   (r["sign_a"] == 172 and r["sign_b"] == 304) or
                   (r["sign_a"] == 304 and r["sign_b"] == 172)), None)
    if target:
        out.append(f"\nPRIMARY TARGET: M172-M304 (PMI={target['pmi']})")
        out.append(f"  Inscriptions with both signs: {target['n_with_pair']}")
        out.append(f"  Dominant motif: {target['top_motif']} ({target['top_motif_%']}% vs {target['base_%']}% baseline)")
        out.append(f"  Enrichment: {target['enrichment_x']}x  p={target['p_value']}")
        if isinstance(target['p_value'], str) and target['p_value'] != 'n/a':
            pf = float(target['p_value'])
            if pf < 0.05:
                out.append(f"  ** SIGNIFICANT: M172-M304 cluster on {target['top_motif']} (p={target['p_value']}) **")
            else:
                out.append(f"  Not significant at p<0.05 — motif link not confirmed")
    else:
        out.append("\nM172-M304 not in top PMI pairs — check mi_edges.csv")

    summary = "\n".join(out)
    print("\n" + summary)

    summary_path = os.path.join(RESULTS_DIR, "motif_summary.txt")
    with open(summary_path, "w") as f:
        f.write(summary)
    print(f"\nSaved → {summary_path}")


if __name__ == "__main__":
    main()
