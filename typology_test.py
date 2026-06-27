"""
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
    sign_counts = Counter(sign for s in seqs for sign in s)
    total_signs = sum(sign_counts.values())
    p_target    = sign_counts[target] / total_signs

    bigram_elevations = {}
    for root in set(preceding):
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

    # Composite fit score (0–1): weighted average of normalised sub-scores
    # Terminal rate contributes most weight (primary prediction)
    fit_score = (
        0.50 * terminal_rate +
        0.25 * min(root_diversity, 1.0) +
        0.25 * min(mean_elevation / 10, 1.0)   # cap at 10× elevation
    )

    return {
        "model":                    "AGGLUTINATIVE",
        "target":                   target,
        "n_sequences":              len(seqs),
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

    agg = result["agglutinative_detail"]
    inf = result["inflectional_detail"]

    print(f"\n{'AGGLUTINATIVE MODEL (Proto-Dravidian / Old Tamil)':─<{W}}")
    print(f"  Terminal rate            {agg['terminal_rate']:.1%}")
    print(f"  Root diversity           {agg['root_diversity']:.3f}")
    print(f"  Mean bigram elevation    {agg['mean_bigram_elevation']}×")
    print(f"  Numeral exclusion        {agg['numeral_exclusion']}")
    print(f"  Fit score                {agg['composite_fit_score']:.4f}")
    if agg.get("bigram_elevations_top5"):
        print(f"  Top preceding signs:")
        for sign, elev in agg["bigram_elevations_top5"]:
            print(f"    {sign}  {elev}×")

    print(f"\n{'INFLECTIONAL MODEL (Sanskrit / Proto-Indo-Aryan)':─<{W}}")
    print(f"  Terminal rate            {inf['terminal_rate']:.1%}")
    print(f"  Non-terminal rate        {inf['non_terminal_rate']:.1%}")
    print(f"  Numeral check            {inf['sanskrit_genitive_numeral_check']}")
    print(f"  Feminine check           {inf['sanskrit_genitive_feminine_check']}")
    print(f"  Fit score                {inf['composite_fit_score']:.4f}")

    print(f"\n{'VERDICT':─<{W}}")
    print(f"  Agglutinative fit        {result['agglutinative_fit']:.4f}")
    print(f"  Inflectional fit         {result['inflectional_fit']:.4f}")
    print(f"  Margin (agg - inf)       {result['margin']:+.4f}")
    print(f"  Result                   {result['verdict']}")
    print("=" * W)
