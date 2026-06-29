"""
Phonetic Mapper — DEDR Anchor Application on Abstract Slot Output
==================================================================
HARD WALL: This script receives abstract slot-tagged sequences from
syntactic_parser.py and sequence_miner.py. It does NOT access the
corpus directly. It does NOT influence slot classification. It is
the ONLY script in the pipeline that knows anything about phonetics.

Architecture (GLM-mandated):
  syntactic_parser.py  →  sign_slots.csv          (slot labels, no phonetics)
  sequence_miner.py    →  sequence_patterns.csv    (sign n-grams, no phonetics)
  phonetic_mapper.py   →  THIS script, receives both, outputs candidates

Mahadevan sign → phonetic anchor table:
  Only entries with DUAL confirmation (Parpola 1994 + ICIT functional label
  OR Parpola 1994 + Keezhadi graffiti match) are included as SAFE.
  All others are marked PREDICTED or UNKNOWN.

Mapping basis:
  M342 → jar sign → P385 → *-an (masculine suffix) [SAFE]
    - ICIT labels Wells 520 as TMK (Terminal Marker)
    - grammar_engine: M342 terminal_rate = 68.0% (highest in corpus)
    - Proof 1: p = 6.54e-21

  M99  → (medial connector sign) → phonetics UNKNOWN
    - medial_rate = 97.0%, freq = 534, but no published phonetic match confirmed
    - Listed as structural sign only

  All other mappings: PREDICTED where Parpola 1994 gives a reading,
  UNKNOWN where no published reading exists.

Outputs:
  results/v3/phonetic_candidates.txt  — candidate readings for top sequences
"""

import csv
import os
from collections import defaultdict

SIGN_SLOTS_PATH    = "results/v3/sign_slots.csv"
SEQ_PATTERNS_PATH  = "results/v3/sequence_patterns.csv"
RESULTS_DIR        = "results/v3"

# ---------------------------------------------------------------------------
# Mahadevan integer → phonetic anchor
# Source: Parpola 1994, Mahadevan 2009, ICIT TMK labels, Keezhadi (Rajan 2025)
# Fields: tamil, roman, ipa, dedr, confidence, grammar_role
# ---------------------------------------------------------------------------
MAHADEVAN_PHONETICS = {
    342: {
        "tamil":        "கணம் / -அன்",
        "roman":        "*kaṇam / -an",
        "ipa":          "/kaɳam/",
        "dedr":         "DEDR-1278",
        "confidence":   "SAFE",
        "grammar_role": "masculine nominal suffix (terminal)",
        "basis":        "Parpola 1994:82 + ICIT TMK label (Wells 520=TMK) + Proof 1 p=6.54e-21",
    },
    # --- PREDICTED anchors (Parpola 1994 tentative, not independently confirmed) ---
    # These are hypotheses, not facts. The mapper flags them clearly.
    # To add a SAFE anchor: requires Parpola 1994 citation + one independent confirmation.
    #
    # M122 = fish sign (Mahadevan concordance plate) → *mīn [SAFE in Parpola]
    # BUT: corpus uses sequential Mahadevan integers from parse_mahadevan.py scrape.
    # The integer for the fish sign in THIS corpus has not been confirmed by
    # manual crosswalk to Parpola P122. Adding as PREDICTED pending verification.
    #
    # Rule: do not guess Mahadevan integers. Only add when explicitly mapped.
}

# Signs confirmed as structural (slot function known, phonetics unknown)
STRUCTURAL_SIGNS = {
    99:  "MEDIAL connector (medial_rate=97.0%, phonetics unconfirmed)",
    267: "INITIAL cluster sign (initial_rate=79.5%, phonetics unconfirmed)",
    87:  "MEDIAL/INITIAL mixed sign (phonetics unconfirmed)",
    176: "TERMINAL sign (terminal_rate=87.5%, phonetics unconfirmed)",
    328: "TERMINAL sign (terminal_rate=86.2%, phonetics unconfirmed)",
}


def load_sign_slots(path):
    """Returns dict: sign(int) -> {slot, count, initial_rate, terminal_rate, medial_rate}"""
    slots = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slots[int(row["sign"])] = {
                "slot":          row["slot"],
                "count":         int(row["count"]),
                "initial_rate":  float(row["initial_rate"]),
                "terminal_rate": float(row["terminal_rate"]),
                "medial_rate":   float(row["medial_rate"]),
            }
    return slots


def load_top_sequences(path, seq_type="sign", max_n=50):
    """Returns top sign n-gram sequences sorted by weighted frequency."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["type"] == seq_type:
                rows.append({
                    "ngram_n":   int(row["ngram_n"]),
                    "signs":     row["signs"],
                    "raw_count": int(row["raw_count"]),
                    "weighted":  float(row["weighted"]),
                })
    rows.sort(key=lambda x: -x["weighted"])
    return rows[:max_n]


def map_sequence(sign_strs, sign_slots):
    """
    Map a sequence of sign strings (e.g. ['M342', 'M99']) to:
      - slot labels
      - phonetic readings (SAFE/PREDICTED/UNKNOWN)
    Returns list of token dicts.
    """
    tokens = []
    for s in sign_strs:
        m_num = int(s.replace("M", ""))
        slot_info = sign_slots.get(m_num, {})
        phonetic  = MAHADEVAN_PHONETICS.get(m_num)
        structural = STRUCTURAL_SIGNS.get(m_num)

        token = {
            "sign":         s,
            "mahadevan_n":  m_num,
            "slot":         slot_info.get("slot", "AMBIGUOUS"),
            "count":        slot_info.get("count", 0),
        }
        if phonetic:
            token["roman"]        = phonetic["roman"]
            token["tamil"]        = phonetic["tamil"]
            token["ipa"]          = phonetic["ipa"]
            token["dedr"]         = phonetic["dedr"]
            token["confidence"]   = phonetic["confidence"]
            token["grammar_role"] = phonetic["grammar_role"]
        elif structural:
            token["roman"]        = "—"
            token["tamil"]        = "—"
            token["ipa"]          = "—"
            token["dedr"]         = "—"
            token["confidence"]   = "STRUCTURAL"
            token["grammar_role"] = structural
        else:
            token["roman"]        = "—"
            token["tamil"]        = "—"
            token["ipa"]          = "—"
            token["dedr"]         = "—"
            token["confidence"]   = "UNKNOWN"
            token["grammar_role"] = "unknown"

        tokens.append(token)
    return tokens


def confidence_score(tokens):
    """
    Returns fraction of tokens with SAFE phonetic reading.
    0.0 = fully unknown, 1.0 = fully confirmed.
    """
    if not tokens:
        return 0.0
    safe = sum(1 for t in tokens if t["confidence"] == "SAFE")
    return safe / len(tokens)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if not os.path.exists(SIGN_SLOTS_PATH):
        print(f"ERROR: {SIGN_SLOTS_PATH} not found. Run syntactic_parser.py first.")
        return
    if not os.path.exists(SEQ_PATTERNS_PATH):
        print(f"ERROR: {SEQ_PATTERNS_PATH} not found. Run sequence_miner.py first.")
        return

    sign_slots = load_sign_slots(SIGN_SLOTS_PATH)
    sequences  = load_top_sequences(SEQ_PATTERNS_PATH, seq_type="sign", max_n=50)

    print(f"Loaded {len(sign_slots)} sign slot labels")
    print(f"Processing top {len(sequences)} sign sequences")

    out = []
    out.append("=" * 72)
    out.append("  PHONETIC MAPPER — DEDR ANCHOR CANDIDATES")
    out.append("  HARD WALL: parser and mapper are separate. Phonetics never")
    out.append("  influenced slot classification above.")
    out.append("=" * 72)
    out.append("")
    out.append("CONFIRMED PHONETIC ANCHORS IN THIS CORPUS")
    out.append(f"  {'Sign':>6}  {'Confidence':12}  {'Reading':20}  {'Role'}")
    out.append("  " + "-" * 64)
    for m_num, p in MAHADEVAN_PHONETICS.items():
        slot = sign_slots.get(m_num, {}).get("slot", "?")
        cnt  = sign_slots.get(m_num, {}).get("count", 0)
        out.append(f"  M{m_num:<5}  [{p['confidence']:10}]  {p['roman']:20s}  "
                   f"{p['grammar_role']}  (slot={slot}, n={cnt})")

    out.append("")
    out.append("STRUCTURAL SIGNS (slot confirmed, phonetics unconfirmed)")
    out.append(f"  {'Sign':>6}  {'Slot':12}  {'Note'}")
    out.append("  " + "-" * 64)
    for m_num, note in STRUCTURAL_SIGNS.items():
        slot = sign_slots.get(m_num, {}).get("slot", "?")
        cnt  = sign_slots.get(m_num, {}).get("count", 0)
        out.append(f"  M{m_num:<5}  {slot:12s}  {note[:55]}  (n={cnt})")

    out.append("")
    out.append("TOP SEQUENCE PHONETIC CANDIDATES")
    out.append("  (Sequences sorted by weighted frequency; SAFE% = fraction")
    out.append("   of signs with independently confirmed phonetic reading)")
    out.append("")

    candidates = []
    for seq in sequences:
        sign_strs = seq["signs"].split("-")
        tokens    = map_sequence(sign_strs, sign_slots)
        safe_pct  = confidence_score(tokens)
        slot_seq  = "-".join(t["slot"][0] for t in tokens)  # I/M/T/A abbreviation
        roman_seq = " + ".join(
            t["roman"] if t["roman"] != "—" else f"{t['sign']}[?]"
            for t in tokens
        )
        candidates.append({
            "seq":       seq,
            "tokens":    tokens,
            "safe_pct":  safe_pct,
            "slot_seq":  slot_seq,
            "roman_seq": roman_seq,
        })

    # Sort: fully SAFE first, then partially known, then unknown
    candidates.sort(key=lambda x: -x["safe_pct"])

    for c in candidates[:30]:
        seq      = c["seq"]
        out.append(f"  {seq['signs']:30s}  raw={seq['raw_count']:>4}  "
                   f"wt={seq['weighted']:>7.4f}  slots={c['slot_seq']}  "
                   f"SAFE={c['safe_pct']*100:.0f}%")
        out.append(f"    Reading: {c['roman_seq']}")
        out.append("")

    out.append("")
    out.append("HONEST ASSESSMENT")
    n_safe = sum(1 for c in candidates if c["safe_pct"] == 1.0)
    n_partial = sum(1 for c in candidates if 0 < c["safe_pct"] < 1.0)
    n_unknown = sum(1 for c in candidates if c["safe_pct"] == 0.0)
    out.append(f"  Fully confirmed (all tokens SAFE):    {n_safe} sequences")
    out.append(f"  Partially confirmed (some SAFE):      {n_partial} sequences")
    out.append(f"  No phonetic anchor available:         {n_unknown} sequences")
    out.append("")
    out.append("  The low SAFE% reflects the honest state of the field.")
    out.append("  M342 (-an suffix) is the only anchor confirmed by two independent")
    out.append("  sources in this Mahadevan integer corpus. All other phonetic")
    out.append("  readings require a verified Mahadevan-to-Parpola crosswalk")
    out.append("  before they can be promoted from UNKNOWN to PREDICTED or SAFE.")
    out.append("  This is not a failure — it is the correct boundary.")

    result = "\n".join(out)
    print("\n" + result)

    out_path = os.path.join(RESULTS_DIR, "phonetic_candidates.txt")
    with open(out_path, "w") as f:
        f.write(result)
    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
