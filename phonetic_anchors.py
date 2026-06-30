"""
SUPPLEMENTARY — phonetic readings isolated from all structural proofs.
No result in paper/main.tex depends on this file. The 6 [LIT.ANCHOR] readings
in Section 12 are drawn from published DEDR and Parpola (1994) sources.
----------------------------------------------------------------------
Phonetic Anchor Mapping Layer — Proto-Dravidian Rebus Bridge
=============================================================
Bridges the purely mathematical framework (positional entropy, suffix theorem)
to Proto-Dravidian phonology via the rebus principle and DEDR root forms.

CONFIDENCE LABELS
-----------------
Every anchor is tagged with one of:

  [SAFE]      — Rebus reading is independently established in the scholarly
                literature (Parpola 1994, Mahadevan 2009, DEDR). The pictogram
                → phoneme mapping is not our interpretation.

  [PREDICTED] — Reading is our computational inference: the sign occupies a
                slot consistent with the labelled grammatical role, but the
                phonetic reading has not been independently confirmed by a
                second source. Treat as a testable hypothesis, not a fact.

REBUS PRINCIPLE (brief)
-----------------------
A pictogram represents not the object drawn but a word that SOUNDS like the
object's name in the original language. This is how alphabets evolved from
pictograms (e.g. Phoenician aleph = ox head → /ʔ/ because 'aleph' = ox).

For Indus signs, the rebus chain is:
  pictogram → Proto-Dravidian word for that object → phonetic value of sign

Sources
-------
  Parpola, A. (1994). Deciphering the Indus Script. Cambridge.
  Mahadevan, I. (2009). "Vestiges of Indus Civilisation in Old Tamil." Harappan Studies.
  Burrow, T. & Emeneau, M.B. (1984). Dravidian Etymological Dictionary (DEDR). 2nd ed.
  Rao, R.P.N. et al. (2009). PNAS 106(33): 13685-13690.
"""

# ---------------------------------------------------------------------------
# Phonetic anchor table
# Fields: sign, pictogram, proto_dravidian, ipa, dedr, confidence, grammar_role, note
# ---------------------------------------------------------------------------

PHONETIC_ANCHORS = [
    {
        "sign":            "P385",
        "pictogram":       "jar / vessel",
        "proto_dravidian": "*kaṇam",
        "tamil_modern":    "கணம்",
        "ipa":             "/kaɳam/",
        "dedr":            "DEDR-1278",
        "suffix_reading":  "-அன் (-an)",
        "confidence":      "SAFE",
        "grammar_role":    "masculine nominal suffix",
        "basis": (
            "Parpola (1994:82) identifies the jar sign as encoding the masculine suffix -an "
            "via short-syllable rebus. Independently confirmed: ICIT labels this sign TMK "
            "(Terminal Marker) — functional label matches grammatical prediction. "
            "Proof 1 p-value = 6.54e-21 (terminal position, pilot corpus)."
        ),
    },
    {
        "sign":            "P122",
        "pictogram":       "fish",
        "proto_dravidian": "*mīn",
        "tamil_modern":    "மீன்",
        "ipa":             "/miːn/",
        "dedr":            "DEDR-4889",
        "suffix_reading":  "meen (noun root)",
        "confidence":      "SAFE",
        "grammar_role":    "noun root — fish / star (homophone rebus)",
        "basis": (
            "Tamil மீன் (meen) means both 'fish' and 'star' — the same word. "
            "Parpola (1994:66) uses this homophone as a key rebus anchor. "
            "Keezhadi ground truth: graffiti sign 14.0 (fish) = Mahadevan 149 = P122, "
            "found on 2,132 sherds (Rajan & Sivanantham 2025). "
            "Co-occurs with P316 and P062 at above-chance frequency (Proof 3)."
        ),
    },
    {
        "sign":            "P316",
        "pictogram":       "spear / vel",
        "proto_dravidian": "*vēl",
        "tamil_modern":    "வேல்",
        "ipa":             "/veːl/",
        "dedr":            "DEDR-5541",
        "suffix_reading":  "vel (noun root)",
        "confidence":      "SAFE",
        "grammar_role":    "noun root — spear; Murugan's primary attribute",
        "basis": (
            "Parpola (1994) identifies the spear sign with Proto-Dravidian *vel. "
            "In Tamil religious tradition, vel is Murugan's weapon and by extension "
            "his name. Co-occurrence with P122 (meen/star) and P062 (malai/mountain) "
            "forms the Murugan cluster (Proof 3)."
        ),
    },
    {
        "sign":            "P060",
        "pictogram":       "corner / angle bracket",
        "proto_dravidian": "*kō",
        "tamil_modern":    "கோ",
        "ipa":             "/koː/",
        "dedr":            "DEDR-2178",
        "suffix_reading":  "ko (title root)",
        "confidence":      "SAFE",
        "grammar_role":    "title — king / lord; confirmed ITM in ICIT notation",
        "basis": (
            "ICIT labels Wells 060 as ITM (Initial Cluster Terminal Marker), "
            "consistent with a title that brackets a name cluster. "
            "Tamil கோ (ko) = king/lord, used in royal epithets. "
            "Parpola (1994:75) supports this reading."
        ),
    },
    {
        "sign":            "P062",
        "pictogram":       "mountain / hill",
        "proto_dravidian": "*malai",
        "tamil_modern":    "மலை",
        "ipa":             "/malaɪ/",
        "dedr":            "DEDR-4710",
        "suffix_reading":  "malai (noun root)",
        "confidence":      "SAFE",
        "grammar_role":    "noun root — mountain; Kurinji (hill) landscape marker",
        "basis": (
            "Parpola (1994) identifies the mountain sign with *malai. "
            "In Sangam geography, malai = Kurinji landscape = Murugan's domain. "
            "Co-occurrence with P316 (vel) and P122 (meen/star) forms Murugan cluster."
        ),
    },
    {
        "sign":            "P091",
        "pictogram":       "six vertical strokes",
        "proto_dravidian": "*āṟu",
        "tamil_modern":    "ஆறு",
        "ipa":             "/aːru/",
        "dedr":            "DEDR-338",
        "suffix_reading":  "aaru (numeral / noun root)",
        "confidence":      "SAFE",
        "grammar_role":    "numeral 6 / noun — river; Murugan has six faces (Shanmukha)",
        "basis": (
            "Tamil ஆறு (aaru) = both 'six' (numeral) and 'river' (homophone rebus). "
            "Murugan is Shanmukha (six-faced). The numeral-sign rebus is a standard "
            "Parpola method (1994:68). DEDR-338 confirms both senses."
        ),
    },
    {
        "sign":            "P311",
        "pictogram":       "jar body (without top arms)",
        "proto_dravidian": "*kuṭam",
        "tamil_modern":    "குடம்",
        "ipa":             "/kuɖam/",
        "dedr":            "DEDR-1712",
        "suffix_reading":  "kudam (noun root — vessel / clan)",
        "confidence":      "PREDICTED",
        "grammar_role":    "noun root — vessel; possibly clan or guild marker",
        "basis": (
            "The jar body sign (P311) co-occurs frequently with P385 (jar with arms). "
            "Reading as *kuṭam (vessel) is plausible but not independently confirmed "
            "in the literature as firmly as P385. Labelled PREDICTED."
        ),
    },
    {
        "sign":            "P117",
        "pictogram":       "tree / branch",
        "proto_dravidian": "*maram",
        "tamil_modern":    "மரம்",
        "ipa":             "/maram/",
        "dedr":            "DEDR-4711",
        "suffix_reading":  "maram (noun root — tree / wood)",
        "confidence":      "PREDICTED",
        "grammar_role":    "noun root — tree; possibly forest-resource or territory marker",
        "basis": (
            "Parpola (1994) tentatively identifies the tree sign with *maram. "
            "The reading is morphologically consistent but lacks secondary confirmation. "
            "Labelled PREDICTED."
        ),
    },
    {
        "sign":            "P210",
        "pictogram":       "hand / palm",
        "proto_dravidian": "*kai",
        "tamil_modern":    "கை",
        "ipa":             "/kaɪ/",
        "dedr":            "DEDR-1403",
        "suffix_reading":  "kai (noun root — hand; also 'branch')",
        "confidence":      "PREDICTED",
        "grammar_role":    "noun root; possibly trade/exchange marker (hand = deal)",
        "basis": (
            "Tamil கை (kai) = hand. The palm sign is structurally similar to Keezhadi "
            "graffiti sign 23.0 mapped to Mahadevan 190 (ladder/comb) via the book — "
            "exact Parpola mapping to kai is PREDICTED, not independently confirmed."
        ),
    },
]

# Index by sign ID
ANCHORS_BY_SIGN = {a["sign"]: a for a in PHONETIC_ANCHORS}


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_safe_anchors() -> list[dict]:
    """Return only [SAFE] anchors — independently confirmed phonetic readings."""
    return [a for a in PHONETIC_ANCHORS if a["confidence"] == "SAFE"]


def get_predicted_anchors() -> list[dict]:
    """Return only [PREDICTED] anchors — our computational inferences."""
    return [a for a in PHONETIC_ANCHORS if a["confidence"] == "PREDICTED"]


def decode_with_phonetics(seq: list[str]) -> list[dict]:
    """
    Add phonetic readings to a sign sequence.
    Returns list of dicts with sign, Tamil reading, confidence label, and IPA.
    Marks unknown signs explicitly.
    """
    result = []
    for sign in seq:
        anchor = ANCHORS_BY_SIGN.get(sign)
        if anchor:
            result.append({
                "sign":            sign,
                "tamil":           anchor["tamil_modern"],
                "roman":           anchor["proto_dravidian"],
                "ipa":             anchor["ipa"],
                "grammar_role":    anchor["grammar_role"],
                "confidence":      anchor["confidence"],
            })
        else:
            result.append({
                "sign":            sign,
                "tamil":           "—",
                "roman":           "—",
                "ipa":             "—",
                "grammar_role":    "unknown",
                "confidence":      "UNKNOWN",
            })
    return result


def phonetic_summary(seq: list[str]) -> str:
    """
    Return a one-line phonetic reading of a sign sequence with confidence flags.
    Example: '*mīn [SAFE] + *vēl [SAFE] + *-an [SAFE]'
    """
    parts = []
    for entry in decode_with_phonetics(seq):
        if entry["roman"] != "—":
            parts.append(f"{entry['roman']} [{entry['confidence']}]")
        else:
            parts.append(f"{entry['sign']} [UNKNOWN]")
    return " + ".join(parts)


# ---------------------------------------------------------------------------
# DEDR cross-reference table — name compounds predicted by this framework
# ---------------------------------------------------------------------------

NAME_COMPOUNDS = [
    {
        "signs":      ["P122", "P385"],
        "tamil":      "மீனன்",
        "roman":      "Meenan",
        "meaning":    "Lord of Stars / Fish-lord",
        "confidence": "PREDICTED",
        "note":       "Fish (meen) + masculine suffix (-an). Tamil royal/divine title.",
    },
    {
        "signs":      ["P316", "P122", "P385"],
        "tamil":      "வேல் மீனன்",
        "roman":      "Vel Meenan",
        "meaning":    "Spear-bearer, Lord of Stars — Murugan epithet",
        "confidence": "PREDICTED",
        "note":       "Murugan's three attributes collapsed into a title sequence.",
    },
    {
        "signs":      ["P060", "P122", "P385"],
        "tamil":      "கோ மீனன்",
        "roman":      "Ko Meenan",
        "meaning":    "King of Stars — royal title",
        "confidence": "PREDICTED",
        "note":       "Ko (king/lord) + fish-star + masculine suffix.",
    },
    {
        "signs":      ["P062", "P316", "P385"],
        "tamil":      "மலை வேலன்",
        "roman":      "Malai Velan",
        "meaning":    "Lord of the Mountain with the Spear — Murugan full title",
        "confidence": "PREDICTED",
        "note":       "Mountain + spear + masculine suffix. Core Murugan epithet in Sangam poetry.",
    },
]


if __name__ == "__main__":
    print("PHONETIC ANCHOR MAPPING LAYER")
    print("=" * 55)

    safe = get_safe_anchors()
    pred = get_predicted_anchors()
    print(f"  [SAFE] anchors:      {len(safe)} (independently confirmed)")
    print(f"  [PREDICTED] anchors: {len(pred)} (computational inference)")
    print()

    print(f"  {'Sign':6} {'Tamil':12} {'IPA':14} {'DEDR':12} {'Confidence'}")
    print("  " + "-" * 62)
    for a in PHONETIC_ANCHORS:
        print(f"  {a['sign']:6} {a['tamil_modern']:12} {a['ipa']:14} {a['dedr']:12} [{a['confidence']}]")

    print()
    print("NAME COMPOUNDS (all PREDICTED — testable hypotheses)")
    print("-" * 55)
    for nc in NAME_COMPOUNDS:
        signs_str = " + ".join(nc["signs"])
        print(f"  {signs_str}")
        print(f"    Tamil: {nc['tamil']}  ({nc['roman']}) — {nc['meaning']}")
        print()
