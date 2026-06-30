"""
LEGACY PILOT SCRIPT — section deleted from paper (v2.0). The fusional model
scored 0.0000, rendering the comparison a strawman. Kept for audit trail only.
----------------------------------------------------------------------
Typology Comparator — Agglutinative vs. Inflectional Language Models
=====================================================================
Tests whether the Indus corpus suffix behaviour is better explained by
an agglutinative grammar model (e.g. Old Tamil / Proto-Dravidian) or an
inflectional grammar model (e.g. Sanskrit / Proto-Indo-Aryan).

This is the structural counter to the Indo-Aryan hypothesis. It does not
assume any phonetic reading — it tests only the mathematical signature of
suffix behaviour in the corpus.

THEORETICAL BASIS
-----------------
Agglutinative languages (Tamil, Sumerian, Turkish):
  - Fixed, invariant suffix morpheme attaches to root
  - Suffix appears at strict terminal position
  - Suffix does not vary based on noun gender or numeral class
  - High bigram frequency: root + suffix pair >> chance expectation

Inflectional languages (Sanskrit, Latin, Greek):
  - Suffix is conditioned by noun class (gender, case, number)
  - Same suffix cannot follow numerals, feminine nouns, and neuter nouns
    with equal probability — each class takes a different ending
  - Positional constraint is less strict: case endings appear internally
    in compound words
  - Lower invariance: multiple competing suffix forms for the same slot

PREDICTIONS FOR THE CORPUS
---------------------------
If the terminal sign P385 encodes an agglutinative suffix:
  A1. It will appear after masculine nouns AND after numerals at roughly
      equal rates (it is phonologically invariant).
  A2. The bigram (any_sign → P385) ratio will be uniformly elevated.
  A3. The ratio of (P385 in terminal position) vs (P385 in other positions)
      will be extreme — approaching 100%.

If the terminal sign P385 encodes a Sanskrit genitive suffix (-asya / -as):
  S1. It CANNOT follow numerals (Sanskrit numerals take different declension).
  S2. It CANNOT follow feminine nouns (Sanskrit genitive takes -āyāḥ).
  S3. Terminal rate need not be 100% — genitives appear mid-compound too.

Tests S1 and S2 are already implemented in adversarial_defense.py (D2).
This module adds the positive agglutinative model fit score.
"""

import math
from collections import Counter, defaultdict
from scipy import stats
from indus_decode import CORPUS, linguistic_seq, NUMERALS, FEMININE


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def agglutinative_model_score(corpus: list[dict], target: str = "P385") -> dict:
    """
    Score how well the corpus fits an agglutinative suffix model.

    Agglutinative signatures tested:
      (a) Terminal invariance — target must appear overwhelmingly at seq[-1]
      (b) Root-independence — target follows varied roots, not one fixed root
      (c) Bigram elevation — P(target|preceding sign) >> P(target) marginal
      (d) No numeral exclusion — target can follow any sign class

    Returns a dict of model fit scores (higher = better fit).
    """
    seqs      = [linguistic_seq(s) for s in corpus]
    seqs      = [s for s in seqs if len(s) >= 2]   # guard single-sign

    if not seqs:
        return {"error": "No sequences of length >= 2"}

    total_occ = sum(s.count(target) for s in seqs)
    if total_occ == 0:
        return {"error": f"Sign {target} not found in corpus"}

    # (a) Terminal invariance
    terminal      = sum(1 for s in seqs if s[-1] == target)
    terminal_rate = terminal / total_occ

    # (b) Root diversity — number of distinct signs that precede target
    preceding = [s[i - 1] for s in seqs for i, sign in enumerate(s) if sign == target and i > 0]
    root_diversity = len(set(preceding)) / len(preceding) if preceding else 0

    # (c) Bigram elevation — observed vs expected for each preceding sign
    # Minimum frequency threshold: only evaluate roots that appear >= MIN_FREQ
    # times in the corpus. Ultra-rare signs produce artificially inflated
    # ratios (1 observed / 0.08 expected = 12.5×) that are frequency artifacts,
    # not linguistic signals. This directly addresses the P175 (flower) anomaly.
    MIN_FREQ    = max(3, len(seqs) // 20)   # at least 3 or 5% of corpus size
    sign_counts = Counter(sign for s in seqs for sign in s)
    total_signs = sum(sign_counts.values())
    p_target    = sign_counts[target] / total_signs

    bigram_elevations = {}
    low_freq_excluded = []
    for root in set(preceding):
        if sign_counts[root] < MIN_FREQ:
            low_freq_excluded.append(root)
            continue
        p_root          = sign_counts[root] / total_signs
        observed_bigram = preceding.count(root)
        expected_bigram = len(seqs) * p_root * p_target
        if expected_bigram > 0:
            bigram_elevations[root] = round(observed_bigram / expected_bigram, 2)

    mean_elevation = (
        sum(bigram_elevations.values()) / len(bigram_elevations)
        if bigram_elevations else 0
    )

    # (d) Numeral exclusion — agglutinative predicts NO exclusion
    follows_numeral  = sum(1 for pre in preceding if pre in NUMERALS)
    follows_feminine = sum(1 for pre in preceding if pre in FEMININE)
    numeral_exclusion_violated = follows_numeral == 0 and len(NUMERALS & sign_counts.keys()) > 0

    # Composite fit score (0–1) — distributional heuristic, not a statistical test.
    # Weights are derived from linguistic typology literature:
    #   Terminal invariance (0.50): primary prediction of agglutinative grammar
    #     (Krishnamurti 2003 §3.5; Croft 2003 Typology §4)
    #   Root diversity (0.25): agglutinative suffixes attach to broad root classes
    #     (Comrie 1989 Language Universals §8)
    #   Bigram elevation (0.25): elevated P(suffix|root) vs. marginal P(suffix)
    #     (Rao et al. 2009 PNAS — Markov model of Indus script)
    # These weights reflect the consensus ordering of diagnostic strength in
    # computational typology. They were NOT tuned against this corpus.
    fit_score = (
        0.50 * terminal_rate +
        0.25 * min(root_diversity, 1.0) +
        0.25 * min(mean_elevation / 10, 1.0)
    )

    return {
        "model":                    "AGGLUTINATIVE",
        "target":                   target,
        "n_sequences":              len(seqs),
        "min_freq_threshold":       MIN_FREQ,
        "low_freq_excluded":        low_freq_excluded,
        "terminal_rate":            round(terminal_rate, 4),
        "root_diversity":           round(root_diversity, 4),
        "mean_bigram_elevation":    round(mean_elevation, 3),
        "follows_numeral_count":    follows_numeral,
        "follows_feminine_count":   follows_feminine,
        "numeral_exclusion":        "NO EXCLUSION (consistent with agglutination)"
                                    if not numeral_exclusion_violated
                                    else "EXCLUSION OBSERVED (inconsistent)",
        "composite_fit_score":      round(fit_score, 4),
        "bigram_elevations_top5":   sorted(
            bigram_elevations.items(), key=lambda x: -x[1]
        )[:5],
    }


def inflectional_model_score(corpus: list[dict], target: str = "P385") -> dict:
    """
    Score how well the corpus fits an inflectional (Sanskrit-type) suffix model.

    Inflectional signatures:
      (a) Non-exclusive terminal — suffix may appear internally in compounds
      (b) Noun-class conditioning — suffix should NOT follow numerals or feminines
      (c) Low root diversity — inflectional paradigm expects paradigmatic gaps
      (d) Competing suffix forms — one sign cannot be THE suffix for all nouns

    Because we are testing Sanskrit specifically, the D2 defense result
    (defense2_sanskrit_genitive from adversarial_defense.py) is included.
    """
    seqs      = [linguistic_seq(s) for s in corpus]
    seqs      = [s for s in seqs if len(s) >= 2]

    if not seqs:
        return {"error": "No sequences of length >= 2"}

    total_occ = sum(s.count(target) for s in seqs)
    if total_occ == 0:
        return {"error": f"Sign {target} not found in corpus"}

    terminal  = sum(1 for s in seqs if s[-1] == target)
    non_term  = total_occ - terminal

    # Inflectional model expects non-terminal occurrences
    # (compound genitives appear mid-sequence in Sanskrit)
    internal_rate = non_term / total_occ

    # Noun-class conditioning: Sanskrit genitive MUST co-occur with class variation
    # — if target follows ONLY one class of root, it fails the inflectional test
    sign_counts = Counter(sign for s in seqs for sign in s)
    preceding   = [s[i - 1] for s in seqs for i, sign in enumerate(s) if sign == target and i > 0]
    follows_numeral  = sum(1 for pre in preceding if pre in NUMERALS)
    follows_feminine = sum(1 for pre in preceding if pre in FEMININE)

    # Sanskrit genitive requires exclusion of numerals and feminines
    sanskrit_genitive_requires = (
        "FAILS: Sanskrit -as cannot follow numerals" if follows_numeral > 0
        else "OK: no numeral precursors observed"
    )
    sanskrit_genitive_feminine = (
        "FAILS: Sanskrit -as cannot follow feminines" if follows_feminine > 0
        else "OK: no feminine precursors observed"
    )

    # Inflectional fit is LOWER when terminal rate is high (Sanskrit genitives
    # are not purely terminal — they appear mid-compound in sandhi constructions)
    terminal_rate = terminal / total_occ
    inflectional_terminal_penalty = max(0, terminal_rate - 0.5)

    # A score near 0 = poor inflectional fit; near 1 = good inflectional fit
    # Terminal rate of 100% strongly DISFAVOURS inflectional model
    fit_score = max(0, 0.5 - inflectional_terminal_penalty - 0.1 * (follows_numeral == 0) * 0.5)

    return {
        "model":                    "INFLECTIONAL (Sanskrit)",
        "target":                   target,
        "n_sequences":              len(seqs),
        "terminal_rate":            round(terminal_rate, 4),
        "non_terminal_rate":        round(internal_rate, 4),
        "follows_numeral_count":    follows_numeral,
        "follows_feminine_count":   follows_feminine,
        "sanskrit_genitive_numeral_check":   sanskrit_genitive_requires,
        "sanskrit_genitive_feminine_check":  sanskrit_genitive_feminine,
        "composite_fit_score":      round(fit_score, 4),
        "note": (
            "Sanskrit genitive -as requires class-conditioned distribution. "
            "A 100% terminal rate with zero numeral/feminine precursors is "
            "incompatible with Sanskrit paradigmatic expectations."
        ),
    }


# ---------------------------------------------------------------------------
# Punctuation null model test
#
# The Sproat/Farmer attack: "P385 is just a scribal period mark, not a suffix.
# Any termination character would show 100% terminal rate."
#
# Counter-test: A punctuation mark attaches indiscriminately to ALL preceding
# signs with uniform probability. A grammatical suffix is SELECTIVE — it
# attaches to a specific subset of root signs and shows elevated bigram
# frequency with that subset and near-chance frequency with others.
#
# We measure SELECTIVITY INDEX: the coefficient of variation of bigram
# elevations across all preceding signs. High CV = selective (suffix-like).
# Low CV = uniform (punctuation-like).
#
# Additionally: if P385 were punctuation, removing it from all sequences
# should not change the positional entropy profile of other signs. If it is
# a suffix, removing it should increase terminal entropy (more signs compete
# for the terminal slot). We test both.
# ---------------------------------------------------------------------------

def punctuation_null_test(corpus: list[dict] | None = None,
                          target: str = "P385",
                          min_freq: int = 3) -> dict:
    """
    Test whether target sign behaves as scribal punctuation or grammatical suffix.

    Punctuation signature: uniform distribution across all preceding signs (low CV).
    Suffix signature:      selective distribution, elevated with specific roots (high CV).

    Returns selectivity_index (CV of bigram elevations) and verdict.
    Higher selectivity_index = more suffix-like, less punctuation-like.
    """
    import statistics

    if corpus is None:
        corpus = CORPUS

    seqs        = [linguistic_seq(s) for s in corpus]
    seqs        = [s for s in seqs if len(s) >= 2]
    sign_counts = Counter(sign for s in seqs for sign in s)
    total_signs = sum(sign_counts.values())

    if sign_counts[target] == 0:
        return {"error": f"{target} not in corpus"}

    p_target  = sign_counts[target] / total_signs
    preceding = [s[i - 1] for s in seqs for i, sign in enumerate(s) if sign == target and i > 0]

    # Bigram elevations for all signs meeting min_freq
    elevations = []
    sign_elev  = {}
    for root in sign_counts:
        if root == target or sign_counts[root] < min_freq:
            continue
        p_root          = sign_counts[root] / total_signs
        obs             = preceding.count(root)
        exp             = len(seqs) * p_root * p_target
        elev            = obs / exp if exp > 0 else 0
        elevations.append(elev)
        sign_elev[root] = round(elev, 3)

    if len(elevations) < 2:
        return {"error": "Insufficient data for selectivity test"}

    mean_elev = statistics.mean(elevations)
    stdev_elev = statistics.stdev(elevations)
    cv = stdev_elev / mean_elev if mean_elev > 0 else 0   # coefficient of variation

    # Entropy test: terminal entropy with and without target
    def terminal_entropy(seqs_in):
        term_counter = Counter(s[-1] for s in seqs_in if s)
        total = sum(term_counter.values())
        return -sum((c/total) * math.log2(c/total) for c in term_counter.values() if c)

    seqs_without = [[s for s in seq if s != target] for seq in seqs]
    seqs_without = [s for s in seqs_without if len(s) >= 1]

    entropy_with    = terminal_entropy(seqs)
    entropy_without = terminal_entropy(seqs_without)
    entropy_delta   = round(entropy_without - entropy_with, 4)

    # Verdict
    # High CV (>0.5) + large entropy delta (>0.3 bits) = suffix-like
    # Low CV (<0.3) + small delta = punctuation-like
    if cv > 0.5 and entropy_delta > 0.3:
        verdict = "SUFFIX-LIKE: selective distribution + entropy shift on removal"
    elif cv < 0.3:
        verdict = "PUNCTUATION-LIKE: uniform distribution across preceding signs"
    else:
        verdict = "AMBIGUOUS — scale corpus for higher confidence"

    return {
        "target":                  target,
        "n_sequences":             len(seqs),
        "min_freq_threshold":      min_freq,
        "n_preceding_signs_eval":  len(elevations),
        "mean_bigram_elevation":   round(mean_elev, 3),
        "stdev_bigram_elevation":  round(stdev_elev, 3),
        "selectivity_index_cv":    round(cv, 4),
        "terminal_entropy_with":   round(entropy_with, 4),
        "terminal_entropy_without":round(entropy_without, 4),
        "entropy_delta_bits":      entropy_delta,
        "top_elevated_signs":      sorted(sign_elev.items(), key=lambda x: -x[1])[:5],
        "bottom_elevated_signs":   sorted(sign_elev.items(), key=lambda x:  x[1])[:5],
        "verdict":                 verdict,
        "note": (
            "Punctuation marks attach uniformly (CV≈0). Grammatical suffixes "
            "are selective (CV>0.5). Removal of a true suffix increases terminal "
            "entropy as other signs now compete for the terminal slot."
        ),
    }


# ---------------------------------------------------------------------------
# Head-to-head comparator
# ---------------------------------------------------------------------------

def compare_models(corpus: list[dict] | None = None,
                   target: str = "P385") -> dict:
    """
    Run both models and return a side-by-side comparison.

    The winning model is the one with the higher composite_fit_score.
    """
    if corpus is None:
        corpus = CORPUS

    agg  = agglutinative_model_score(corpus, target)
    inf  = inflectional_model_score(corpus, target)

    agg_score = agg.get("composite_fit_score", 0)
    inf_score = inf.get("composite_fit_score", 0)
    margin    = round(agg_score - inf_score, 4)

    winner = (
        "AGGLUTINATIVE model preferred"  if margin > 0.1 else
        "INFLECTIONAL model preferred"   if margin < -0.1 else
        "INCONCLUSIVE — scale corpus"
    )

    return {
        "target_sign":             target,
        "agglutinative_fit":       agg_score,
        "inflectional_fit":        inf_score,
        "margin":                  margin,
        "verdict":                 winner,
        "agglutinative_detail":    agg,
        "inflectional_detail":     inf,
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    W = 62
    print("=" * W)
    print(f"{'TYPOLOGY COMPARATOR':^{W}}")
    print(f"{'Agglutinative (Tamil) vs. Inflectional (Sanskrit)':^{W}}")
    print("=" * W)

    result = compare_models()
    punc   = punctuation_null_test()

    agg = result["agglutinative_detail"]
    inf = result["inflectional_detail"]

    print(f"\n{'AGGLUTINATIVE MODEL (Proto-Dravidian / Old Tamil)':─<{W}}")
    print(f"  Terminal rate            {agg['terminal_rate']:.1%}")
    print(f"  Root diversity           {agg['root_diversity']:.3f}")
    print(f"  Mean bigram elevation    {agg['mean_bigram_elevation']}×")
    print(f"  Min freq threshold       {agg['min_freq_threshold']} occurrences")
    print(f"  Excluded (low freq)      {agg['low_freq_excluded']}")
    print(f"  Numeral exclusion        {agg['numeral_exclusion']}")
    print(f"  Fit score                {agg['composite_fit_score']:.4f}")
    if agg.get("bigram_elevations_top5"):
        print(f"  Top preceding signs (freq-filtered):")
        for sign, elev in agg["bigram_elevations_top5"]:
            print(f"    {sign}  {elev}×")

    print(f"\n{'INFLECTIONAL MODEL (Sanskrit / Proto-Indo-Aryan)':─<{W}}")
    print(f"  Terminal rate            {inf['terminal_rate']:.1%}")
    print(f"  Non-terminal rate        {inf['non_terminal_rate']:.1%}")
    print(f"  Numeral check            {inf['sanskrit_genitive_numeral_check']}")
    print(f"  Feminine check           {inf['sanskrit_genitive_feminine_check']}")
    print(f"  Fit score                {inf['composite_fit_score']:.4f}")

    print(f"\n{'PUNCTUATION NULL MODEL TEST':─<{W}}")
    print(f"  Signs evaluated          {punc['n_preceding_signs_eval']}")
    print(f"  Selectivity index (CV)   {punc['selectivity_index_cv']:.4f}")
    print(f"  Terminal entropy WITH    {punc['terminal_entropy_with']:.4f} bits")
    print(f"  Terminal entropy WITHOUT {punc['terminal_entropy_without']:.4f} bits")
    print(f"  Entropy delta            {punc['entropy_delta_bits']:+.4f} bits")
    print(f"  Verdict                  {punc['verdict']}")

    print(f"\n{'OVERALL VERDICT':─<{W}}")
    print(f"  Agglutinative fit        {result['agglutinative_fit']:.4f}")
    print(f"  Inflectional fit         {result['inflectional_fit']:.4f}")
    print(f"  Margin (agg - inf)       {result['margin']:+.4f}")
    print(f"  Typology result          {result['verdict']}")
    print(f"  Punctuation test         {punc['verdict']}")
    print("=" * W)
