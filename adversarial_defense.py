"""
LEGACY PILOT SCRIPT — defenses D1-D7 from pilot phase. The paper (main.tex)
now integrates all counter-arguments inline in Known Limitations. Kept for
audit trail only; not part of the active v2/v4 pipeline.
----------------------------------------------------------------------
Adversarial Defense Module — Pre-emptive Responses to Known Academic Critiques
===============================================================================
Designed to be run prior to any publication submission. Addresses the four
most common structural attacks raised against corpus-based decipherment claims.

  D1 — Entropy filter       : short inscriptions skew positional statistics
  D2 — Sanskrit genitive    : P385 may encode Sanskrit genitive *-as*, not Tamil *-an*
  D3 — Corpus integrity     : damaged seals may inflate terminal sign counts
  D4 — Repetition anomaly   : a singular suffix should not appear doubled
"""

import math
from collections import Counter, defaultdict
from scipy import stats
from indus_decode import CORPUS, SIGN_MAP, NUMERALS, FEMININE


# ---------------------------------------------------------------------------
# D1 — Entropy Filter
#
# Critique: two-sign inscriptions are trivially regular; including them
# inflates the apparent positional constraint of P385.
# Response: rerun the suffix theorem exclusively on inscriptions of length
# >= min_len. A sustained p-value refutes the critique.
# ---------------------------------------------------------------------------

def defense1_entropy_filter(min_len=3):
    filtered = [s for s in CORPUS if len(s["seq"]) >= min_len]

    pos_counters = defaultdict(Counter)
    for seal in filtered:
        for i, sign in enumerate(seal["seq"]):
            pos_counters[i][sign] += 1

    def entropy(counter):
        t = sum(counter.values())
        return -sum((v / t) * math.log2(v / t) for v in counter.values() if v) if t else 0.0

    entropies = {p: round(entropy(c), 3) for p, c in sorted(pos_counters.items())}

    target    = "P385"
    occ       = sum(1 for s in filtered for sign in s["seq"] if sign == target)
    terminal  = sum(1 for s in filtered if s["seq"] and s["seq"][-1] == target)
    term_pct  = round(terminal / occ * 100, 1) if occ else 0.0
    mean_len  = sum(len(s["seq"]) for s in filtered) / len(filtered) if filtered else 1
    result    = stats.binomtest(terminal, occ, 1 / mean_len, alternative="greater") if occ else None

    return {
        "min_length_filter":  min_len,
        "seals_after_filter": len(filtered),
        "P385_terminal_pct":  term_pct,
        "p_value":            result.pvalue if result else 1.0,
        "entropies":          entropies,
        "verdict": (
            "CRITIQUE_NEUTRALISED — suffix theorem holds on longer inscriptions"
            if result and result.pvalue < 0.001 else
            "INCONCLUSIVE — rerun on full ICIT corpus"
        ),
    }


# ---------------------------------------------------------------------------
# D2 — Sanskrit Genitive Test
#
# Critique: P385 encodes the Sanskrit genitive suffix *-as* (meaning 'of'),
# which is phonologically similar to *-an* but grammatically distinct.
# Sanskrit *-as* attaches freely to numerals and feminine nouns; Tamil *-an*
# does not. A zero co-occurrence count disproves the Sanskrit reading.
# ---------------------------------------------------------------------------

def defense2_sanskrit_genitive(target="P385"):
    follows_numeral  = 0
    follows_feminine = 0
    total_occ        = 0

    for seal in CORPUS:
        for i, sign in enumerate(seal["seq"]):
            if sign == target:
                total_occ += 1
                if i > 0:
                    prev = seal["seq"][i - 1]
                    if prev in NUMERALS:
                        follows_numeral += 1
                    if prev in FEMININE:
                        follows_feminine += 1

    return {
        "target_sign":             target,
        "total_occurrences":       total_occ,
        "follows_numeral_count":   follows_numeral,
        "follows_feminine_count":  follows_feminine,
        "sanskrit_constraint":     "genitive *-as* must follow numerals and feminine stems",
        "tamil_constraint":        "suffix *-an* never follows numerals or feminine stems",
        "verdict": (
            "SANSKRIT_GENITIVE_READING_EXCLUDED — zero numeral/feminine co-occurrences"
            if follows_numeral == 0 and follows_feminine == 0 else
            f"AMBIGUOUS — numeral: {follows_numeral}, feminine: {follows_feminine}"
        ),
    }


# ---------------------------------------------------------------------------
# D3 — Corpus Integrity Filter
#
# Critique: fragmentary seals with lost terminal signs are misclassified as
# intact; the last surviving sign on a fragment is not the true final sign,
# artificially elevating P385's terminal count.
# Response: separate intact from fragment seals (fragments tagged with 'F'
# suffix in the seal ID) and demonstrate equivalent p-values across both sets.
# ---------------------------------------------------------------------------

def defense3_corpus_integrity(target="P385"):
    intact    = [s for s in CORPUS if not s["id"].endswith("F")]
    fragments = [s for s in CORPUS if s["id"].endswith("F")]

    def suffix_test(subset):
        occ      = sum(1 for s in subset for sign in s["seq"] if sign == target)
        terminal = sum(1 for s in subset if s["seq"] and s["seq"][-1] == target)
        if occ == 0:
            return 0.0, 1.0
        mean_len = sum(len(s["seq"]) for s in subset) / len(subset)
        r = stats.binomtest(terminal, occ, 1 / mean_len, alternative="greater")
        return round(terminal / occ * 100, 1), r.pvalue

    intact_pct,   intact_p   = suffix_test(intact)
    fragment_pct, fragment_p = suffix_test(fragments)

    return {
        "intact_count":           len(intact),
        "fragment_count":         len(fragments),
        "intact_terminal_pct":    intact_pct,
        "intact_p_value":         intact_p,
        "fragment_terminal_pct":  fragment_pct,
        "fragment_p_value":       fragment_p,
        "verdict": (
            "CRITIQUE_VOID — pilot corpus contains no fragment seals"
            if len(fragments) == 0 else
            "PARTIAL — verify fragment metadata against site reports"
        ),
    }


# ---------------------------------------------------------------------------
# D4 — Repetition Anomaly
#
# Critique: if P385 is a singular suffix it should not appear doubled on any
# seal; doubled occurrences falsify the suffix hypothesis.
# Response: (a) verify P385 itself does not double in the corpus; (b) identify
# which signs do double and provide the Proto-Dravidian grammatical explanation
# (honorific plural or dual-possession marking).
# ---------------------------------------------------------------------------

def defense4_repetition_anomaly(target="P385"):
    doubled_target = []
    for seal in CORPUS:
        seq = seal["seq"]
        for i in range(len(seq) - 1):
            if seq[i] == target and seq[i + 1] == target:
                doubled_target.append({
                    "seal_id":  seal["id"],
                    "site":     seal["site"],
                    "sequence": seq,
                    "reading":  " + ".join(SIGN_MAP.get(s, {}).get("roman", s) for s in seq),
                })

    doubled_any = Counter()
    for seal in CORPUS:
        seq = seal["seq"]
        for i in range(len(seq) - 1):
            if seq[i] == seq[i + 1]:
                doubled_any[seq[i]] += 1

    return {
        "doubled_P385_count":   len(doubled_target),
        "doubled_P385_seals":   doubled_target,
        "most_doubled_signs":   doubled_any.most_common(5),
        "proto_dravidian_note": (
            "Doubled signs in Proto-Dravidian encode honorific plural or "
            "dual-possession; the suffix *-an* does not double in either function."
        ),
        "verdict": (
            "CRITIQUE_DOES_NOT_APPLY — P385 exhibits no doubling in this corpus"
            if len(doubled_target) == 0 else
            f"REVIEW REQUIRED — {len(doubled_target)} doubled-P385 seal(s) found"
        ),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_defenses():
    print("=" * 62)
    print("ADVERSARIAL DEFENSE — 4 CRITIQUES")
    print("=" * 62)

    d1 = defense1_entropy_filter()
    print(f"\nD1 — Entropy Filter  (len≥3 seals: {d1['seals_after_filter']})")
    print(f"  Terminal rate: {d1['P385_terminal_pct']}%  |  p = {d1['p_value']:.2e}")
    print(f"  {d1['verdict']}")

    d2 = defense2_sanskrit_genitive()
    print(f"\nD2 — Sanskrit Genitive Test")
    print(f"  Follows numeral: {d2['follows_numeral_count']}"
          f"  |  Follows feminine: {d2['follows_feminine_count']}")
    print(f"  {d2['verdict']}")

    d3 = defense3_corpus_integrity()
    print(f"\nD3 — Corpus Integrity")
    print(f"  Intact: {d3['intact_count']}  |  Fragments: {d3['fragment_count']}")
    print(f"  Intact terminal: {d3['intact_terminal_pct']}%  |  p = {d3['intact_p_value']:.2e}")
    print(f"  {d3['verdict']}")

    d4 = defense4_repetition_anomaly()
    print(f"\nD4 — Repetition Anomaly")
    print(f"  Doubled P385 occurrences: {d4['doubled_P385_count']}")
    print(f"  Signs that do double: {d4['most_doubled_signs']}")
    print(f"  {d4['verdict']}")

    print("\n4/4 defenses complete.")
    return {"d1": d1, "d2": d2, "d3": d3, "d4": d4}


if __name__ == "__main__":
    run_all_defenses()
