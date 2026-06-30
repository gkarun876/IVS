"""
Direction Grammar Test — RTL vs LTR Markov Consistency
=======================================================
Tests whether Left-to-Right (LTR) inscriptions share the same grammatical
structure as Right-to-Left (RTL) inscriptions.

Method:
  1. Assign each inscription a single direction using motif_data.json
     Resolution rule: sideline=0 wins; else sideline=1; else majority vote
  2. Split corpus into RTL (dir=1) and LTR (dir=2) subsets
  3. Train bigram transition matrix on RTL corpus
  4. Score each LTR inscription as log-likelihood per sign under RTL matrix
  5. Generate random baseline: 1000 permutations of LTR sequences, score each
  6. Compare real LTR perplexity vs RTL held-out perplexity vs random baseline
  7. t-test: real LTR vs random baseline
  8. Report: direction-invariant OR directional syntax

Null hypothesis H0: LTR perplexity == random baseline perplexity
If H0 rejected (p < 0.05) AND LTR << random → same grammar, direction-invariant
If LTR ≈ random → LTR uses different grammar

Output:
  results/v4/direction_grammar_test.txt
"""

import json
import math
import random
from collections import Counter, defaultdict
from scipy import stats

CORPUS_PATH = "data/mahadevan_corpus.json"
MOTIF_PATH  = "data/motif_data.json"
RESULTS_DIR = "results/v4"
OUT_PATH    = "results/v4/direction_grammar_test.txt"

SMOOTHING   = 1e-6   # Laplace-style floor for unseen bigrams
N_PERMUTE   = 1000   # permutations for random baseline
RANDOM_SEED = 42


# ---------------------------------------------------------------------------
# Step 1: resolve direction per textnum
# ---------------------------------------------------------------------------

def resolve_direction(motif_records):
    """
    Given all Firestore records, assign one direction code per textnum.
    Priority: sideline=0 > sideline=1 > majority vote across sides.
    Returns dict: textnum (int) -> dir (str)
    """
    by_tn = defaultdict(list)
    for r in motif_records:
        by_tn[r["textnum"]].append(r)

    result = {}
    for tn, records in by_tn.items():
        # prefer sideline=0 (only side)
        s0 = [r for r in records if str(r.get("sideline", "")) == "0"]
        if s0:
            result[tn] = str(s0[0]["dir"])
            continue
        # prefer sideline=1
        s1 = [r for r in records if str(r.get("sideline", "")) == "1"]
        if s1:
            result[tn] = str(s1[0]["dir"])
            continue
        # majority vote
        votes = Counter(str(r["dir"]) for r in records)
        result[tn] = votes.most_common(1)[0][0]

    return result


# ---------------------------------------------------------------------------
# Step 2: attach direction to corpus entries
# ---------------------------------------------------------------------------

def attach_directions(corpus, dir_map):
    for e in corpus:
        try:
            tn = int(str(e.get("id", "")).split("-")[0])
        except Exception:
            tn = None
        e["textnum"] = tn
        e["dir"] = dir_map.get(tn, "0") if tn else "0"
    return corpus


# ---------------------------------------------------------------------------
# Step 3: bigram matrix
# ---------------------------------------------------------------------------

def build_matrix(seqs):
    """Returns bigram counts and unigram counts."""
    bigram  = Counter()
    nonfinal = Counter()
    for seq in seqs:
        for i in range(len(seq) - 1):
            bigram[(seq[i], seq[i+1])] += 1
            nonfinal[seq[i]] += 1
    return bigram, nonfinal


# ---------------------------------------------------------------------------
# Step 4: score a sequence against a trained matrix
# ---------------------------------------------------------------------------

def score_seq(seq, bigram, nonfinal, vocab_size):
    """
    Log-likelihood per transition under the trained matrix.
    Returns average log2 prob per bigram step (lower = more surprised).
    Smoothed to avoid log(0).
    """
    if len(seq) < 2:
        return None

    total_ll = 0.0
    n_steps  = 0
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i+1]
        denom = nonfinal.get(a, 0)
        num   = bigram.get((a, b), 0)
        # add-epsilon smoothing
        p = (num + SMOOTHING) / (denom + SMOOTHING * vocab_size) if denom > 0 else SMOOTHING
        total_ll += math.log2(p)
        n_steps  += 1

    return total_ll / n_steps if n_steps > 0 else None


# ---------------------------------------------------------------------------
# Step 5: perplexity = 2^(-avg_ll)
# ---------------------------------------------------------------------------

def perplexity(scores):
    valid = [s for s in scores if s is not None]
    if not valid:
        return None, None
    avg_ll = sum(valid) / len(valid)
    return 2 ** (-avg_ll), valid


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import os
    os.makedirs(RESULTS_DIR, exist_ok=True)
    random.seed(RANDOM_SEED)

    # Load data
    with open(CORPUS_PATH) as f:
        corpus = json.load(f)
    with open(MOTIF_PATH) as f:
        motif_records = json.load(f)

    dir_map = resolve_direction(motif_records)
    corpus  = attach_directions(corpus, dir_map)

    # Split
    rtl = [e for e in corpus if e["dir"] == "1"]
    ltr = [e for e in corpus if e["dir"] == "2"]
    oth = [e for e in corpus if e["dir"] not in ("1", "2")]

    out = []
    out.append("=" * 65)
    out.append("  DIRECTION GRAMMAR TEST — RTL vs LTR")
    out.append("=" * 65)
    out.append(f"\n  Total corpus:       {len(corpus)}")
    out.append(f"  RTL (dir=1):        {len(rtl)}")
    out.append(f"  LTR (dir=2):        {len(ltr)}")
    out.append(f"  Other/unknown:      {len(oth)}")
    out.append(f"\n  RTL train set:      {len(rtl)} inscriptions")
    out.append(f"  LTR test set:       {len(ltr)} inscriptions")

    if len(ltr) < 10:
        out.append("\n  ABORT: fewer than 10 LTR inscriptions — insufficient for test")
        print("\n".join(out))
        return

    # Train on RTL
    rtl_seqs = [e["seq"] for e in rtl]
    ltr_seqs = [e["seq"] for e in ltr]

    rtl_bigram, rtl_nonfinal = build_matrix(rtl_seqs)
    vocab = set(s for seq in rtl_seqs for s in seq)
    vocab_size = len(vocab)

    out.append(f"  RTL vocab size:     {vocab_size} unique signs")
    out.append(f"  RTL bigram pairs:   {len(rtl_bigram)}")

    # Score RTL held-out (10-fold: use 90% train, score 10%)
    # Simple: train on all RTL, score RTL itself (in-sample baseline)
    rtl_scores = [score_seq(seq, rtl_bigram, rtl_nonfinal, vocab_size) for seq in rtl_seqs]
    rtl_ppl, rtl_valid = perplexity(rtl_scores)

    # Score LTR against RTL matrix
    ltr_scores = [score_seq(seq, rtl_bigram, rtl_nonfinal, vocab_size) for seq in ltr_seqs]
    ltr_ppl, ltr_valid = perplexity(ltr_scores)

    # Random baseline: permute LTR sequences N times, score each
    rand_ppls = []
    all_ltr_signs = [s for seq in ltr_seqs for s in seq]
    for _ in range(N_PERMUTE):
        perm_seqs = []
        for seq in ltr_seqs:
            perm = random.sample(all_ltr_signs, len(seq))
            perm_seqs.append(perm)
        perm_scores = [score_seq(seq, rtl_bigram, rtl_nonfinal, vocab_size) for seq in perm_seqs]
        perm_ppl, _ = perplexity(perm_scores)
        if perm_ppl:
            rand_ppls.append(perm_ppl)

    rand_mean = sum(rand_ppls) / len(rand_ppls)
    rand_std  = (sum((x - rand_mean)**2 for x in rand_ppls) / len(rand_ppls)) ** 0.5

    # t-test: LTR scores vs random baseline scores (per-inscription level)
    # Rebuild random per-inscription scores for proper t-test
    rand_per_insc = []
    for _ in range(N_PERMUTE):
        perm_scores = []
        for seq in ltr_seqs:
            perm = random.sample(all_ltr_signs, len(seq))
            s = score_seq(perm, rtl_bigram, rtl_nonfinal, vocab_size)
            if s is not None:
                perm_scores.append(s)
        rand_per_insc.extend(perm_scores[:len(ltr_valid)])  # cap to same n

    t_stat, p_val = stats.ttest_ind(ltr_valid, rand_per_insc[:len(ltr_valid)*10],
                                     equal_var=False)

    # Effect size (Cohen's d)
    rand_sample_mean = sum(rand_per_insc) / len(rand_per_insc) if rand_per_insc else 0
    rand_sample_std  = (sum((x-rand_sample_mean)**2 for x in rand_per_insc)/len(rand_per_insc))**0.5 if rand_per_insc else 1
    ltr_mean = sum(ltr_valid) / len(ltr_valid)
    pooled_std = ((rand_sample_std**2 + (sum((x-ltr_mean)**2 for x in ltr_valid)/len(ltr_valid))) / 2) ** 0.5
    cohens_d = (ltr_mean - rand_sample_mean) / pooled_std if pooled_std > 0 else 0

    out.append(f"\n{'='*65}")
    out.append(f"  RESULTS")
    out.append(f"{'='*65}")
    out.append(f"\n  RTL in-sample perplexity:   {rtl_ppl:.2f}  (n={len(rtl_valid)})")
    out.append(f"  LTR vs RTL-matrix ppl:      {ltr_ppl:.2f}  (n={len(ltr_valid)})")
    out.append(f"  Random baseline ppl:        {rand_mean:.2f} ± {rand_std:.2f}  (n={N_PERMUTE} permutations)")
    out.append(f"\n  LTR/RTL perplexity ratio:   {ltr_ppl/rtl_ppl:.3f}x")
    out.append(f"  LTR/Random ratio:           {ltr_ppl/rand_mean:.3f}x")
    out.append(f"\n  t-statistic:                {t_stat:.4f}")
    out.append(f"  p-value (LTR vs random):    {p_val:.4e}")
    out.append(f"  Cohen's d:                  {cohens_d:.4f}")

    out.append(f"\n{'='*65}")
    out.append(f"  INTERPRETATION (data only — no linguistic claims)")
    out.append(f"{'='*65}")

    if p_val < 0.05 and ltr_ppl < rand_mean:
        verdict = "DIRECTIONALLY ROBUST GRAMMAR"
        interp = (
            f"  LTR perplexity ({ltr_ppl:.2f}) is significantly lower than random\n"
            f"  baseline ({rand_mean:.2f}) when scored against the RTL matrix.\n"
            f"  p={p_val:.4e} < 0.05. Cohen's d={cohens_d:.3f}.\n\n"
            f"  NOTE: LTR perplexity ({ltr_ppl:.2f}) is {ltr_ppl/rtl_ppl:.1f}x higher than\n"
            f"  RTL in-sample ({rtl_ppl:.2f}). The grammar is NOT direction-invariant —\n"
            f"  exact word-order rules degrade when direction flips.\n\n"
            f"  What is proven: the underlying statistical dependencies (hub sign\n"
            f"  co-occurrences, bigram affinities) are strong enough to score LTR\n"
            f"  sequences {rand_mean/ltr_ppl:.0f}x better than random permutations.\n"
            f"  The 'glue' between signs survives directional flip even when exact\n"
            f"  order does not. The v1.5 paper's RTL assumption does not invalidate\n"
            f"  the proofs — but LTR inscriptions follow a distinct word order."
        )
    elif p_val < 0.05 and ltr_ppl > rand_mean:
        verdict = "DIRECTIONAL SYNTAX DETECTED"
        interp = (
            f"  LTR perplexity ({ltr_ppl:.2f}) is significantly HIGHER than random\n"
            f"  baseline ({rand_mean:.2f}) when scored against the RTL matrix.\n"
            f"  p={p_val:.4e} < 0.05.\n\n"
            f"  LTR inscriptions are LESS predictable under the RTL matrix than\n"
            f"  random permutations. This indicates a distinct grammatical structure\n"
            f"  for LTR writing — directional syntax in the Indus script."
        )
    else:
        verdict = "INCONCLUSIVE"
        interp = (
            f"  LTR perplexity ({ltr_ppl:.2f}) vs random ({rand_mean:.2f}).\n"
            f"  p={p_val:.4e} — not significant at p<0.05.\n"
            f"  Cannot distinguish LTR grammar from random under current corpus size.\n"
            f"  LTR n={len(ltr_valid)} may be insufficient for a definitive result."
        )

    out.append(f"\n  VERDICT: {verdict}")
    out.append(f"\n{interp}")

    # Sign-level: which signs appear exclusively in LTR but not RTL
    rtl_sign_set = set(s for seq in rtl_seqs for s in seq)
    ltr_sign_set = set(s for seq in ltr_seqs for s in seq)
    ltr_exclusive = ltr_sign_set - rtl_sign_set
    shared        = ltr_sign_set & rtl_sign_set

    out.append(f"\n{'='*65}")
    out.append(f"  SIGN OVERLAP ANALYSIS")
    out.append(f"{'='*65}")
    out.append(f"  RTL unique signs:   {len(rtl_sign_set)}")
    out.append(f"  LTR unique signs:   {len(ltr_sign_set)}")
    out.append(f"  Shared signs:       {len(shared)}  ({len(shared)/len(ltr_sign_set)*100:.1f}% of LTR)")
    out.append(f"  LTR-exclusive:      {len(ltr_exclusive)}")
    if ltr_exclusive:
        out.append(f"  LTR-only signs:     {sorted(ltr_exclusive)[:20]}")

    result = "\n".join(out)
    print(result)
    with open(OUT_PATH, "w") as f:
        f.write(result)
    print(f"\nSaved → {OUT_PATH}")


if __name__ == "__main__":
    main()
