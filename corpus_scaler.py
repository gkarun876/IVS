"""
Corpus Scaler — Scaling Proofs to the Full Mahadevan / ICIT Corpus
===================================================================
The pilot corpus in indus_decode.py has 41 seals. That is sufficient for
proof-of-concept but exposes the project to the "small subcorpus" critique.

This module provides three pathways to a larger corpus:

  PATH A — Rao et al. (2009) dataset
    Rao, R.P.N. et al. (2009). "A Markov model of the Indus script."
    PNAS 106(33): 13685-13690.  doi:10.1073/pnas.0906077106
    The authors used a corpus of ~1,000 IVC texts (Mahadevan 1977 base).
    A processed version is available at:
      https://github.com/srajangarg/indus-valley (CSV format)
    Or can be reconstructed from the PNAS supplementary data.

  PATH B — ICIT database (Fuls 2010)
    5,509 inscriptions. Requires login credentials from Andreas Fuls
    (fuls@mailbox.tu-berlin.de). corpus_loader.py handles the import
    once credentials / CSV export are obtained.

  PATH C — Mahadevan 1977 machine-readable transcription
    Several research groups have digitised the Mahadevan concordance.
    The most cited version: Yadav et al. (2010), "Statistical analysis of
    the Indus script using n-grams." PLoS ONE 5(3): e9506.
    Their corpus file (1,548 inscriptions) has been made available by
    some authors on request.

USAGE
-----
  from corpus_scaler import load_rao_csv, scale_proofs

  corpus = load_rao_csv("path/to/rao_corpus.csv")
  scale_proofs(corpus)

Until an external corpus file is provided, scale_proofs() runs on the
pilot corpus and clearly labels all output as PILOT SCALE.
"""

import csv
import os
from indus_decode import CORPUS as PILOT_CORPUS, proof1_suffix_theorem, linguistic_seq

# Mahadevan notation for eroded / unreadable signs
ERODED_TOKENS = {"P000", "000", "0", "?", "X"}


# ---------------------------------------------------------------------------
# Erosion Masking Filter
#
# In the Mahadevan (1977) and ICIT corpora, damaged or unreadable signs are
# recorded as 000 (or P000 after conversion). When an eroded sign appears
# within `radius` positions of a target anchor sign, the bigram or positional
# count for that anchor is unreliable — we don't know what the eroded sign was,
# so we can't know whether the anchor is truly in terminal position or is just
# the last *surviving* sign on a broken seal.
#
# This filter removes such contaminated sequences before statistical analysis.
# It is applied automatically by scale_proofs() and can be called manually.
# ---------------------------------------------------------------------------

def apply_erosion_mask(
    corpus: list[dict],
    anchors: set[str] | None = None,
    radius: int = 2,
    eroded_tokens: set[str] = ERODED_TOKENS,
) -> tuple[list[dict], dict]:
    """
    Remove inscriptions where an eroded sign falls within `radius` positions
    of any sign in `anchors`.

    Parameters
    ----------
    corpus        : list of seal dicts with "seq" field
    anchors       : signs to protect; defaults to {"P385", "P122"} (our key signs)
    radius        : window size around each anchor to check for erosion
    eroded_tokens : sign codes that represent damaged / unreadable signs

    Returns
    -------
    (clean_corpus, report) where report is a dict with masking statistics.
    """
    if anchors is None:
        anchors = {"P385", "P122"}

    clean    = []
    dropped  = []
    reasons  = []

    for seal in corpus:
        seq = linguistic_seq(seal)

        # Find positions of all eroded tokens
        eroded_positions = {i for i, s in enumerate(seq) if s in eroded_tokens}

        if not eroded_positions:
            clean.append(seal)
            continue

        # Check if any eroded position is within `radius` of any anchor
        anchor_positions = {i for i, s in enumerate(seq) if s in anchors}
        contaminated = any(
            abs(ep - ap) <= radius
            for ep in eroded_positions
            for ap in anchor_positions
        )

        if contaminated:
            dropped.append(seal["id"])
            reasons.append({
                "id":              seal["id"],
                "seq":             seq,
                "eroded_at":       sorted(eroded_positions),
                "anchor_at":       sorted(anchor_positions),
            })
        else:
            # Eroded signs exist but not near anchors — keep, strip eroded tokens
            clean_seq = [s for s in seq if s not in eroded_tokens]
            # Guard: drop single-sign remnants — too short for positional analysis
            if len(clean_seq) >= 2:
                patched = dict(seal)
                patched["seq"] = clean_seq
                clean.append(patched)

    report = {
        "input_count":   len(corpus),
        "clean_count":   len(clean),
        "dropped_count": len(dropped),
        "drop_rate_pct": round(len(dropped) / len(corpus) * 100, 1) if corpus else 0,
        "anchors":       sorted(anchors),
        "radius":        radius,
        "dropped_ids":   dropped[:20],   # first 20 for inspection
    }
    return clean, report


# ---------------------------------------------------------------------------
# PATH A — Rao et al. 2009 CSV loader
# Expected columns: text_id, site, signs (space-separated Parpola P-numbers)
# e.g.  M001,Mohenjo-daro,P122 P316 P385
# ---------------------------------------------------------------------------

def load_rao_csv(filepath: str) -> list[dict]:
    """
    Load a corpus CSV in Rao et al. 2009 format.

    Expected columns:
        text_id   — inscription identifier
        site      — site name
        signs     — space-separated Parpola P-numbers (e.g. "P122 P316 P385")

    Returns corpus list compatible with indus_decode proof functions.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Corpus file not found: {filepath}\n"
            "See module docstring for download sources (Rao 2009 / Yadav 2010)."
        )

    corpus = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text_id = row.get("text_id", row.get("id", "")).strip()
            site    = row.get("site", "unknown").strip()
            signs   = row.get("signs", row.get("sign_sequence", "")).strip()

            if not signs:
                continue

            seq = [s.strip() for s in signs.split() if s.strip()]
            if seq:
                corpus.append({"id": text_id, "site": site, "seq": seq})

    print(f"Loaded {len(corpus)} inscriptions from {filepath}")
    return corpus


def load_yadav_csv(filepath: str) -> list[dict]:
    """
    Load a corpus CSV in Yadav et al. 2010 (PLoS ONE) format.

    Expected columns:
        id        — inscription identifier
        signs     — comma or space-separated Mahadevan sign numbers
                    (integers; converted to Pxx format)

    Mahadevan sign numbers are stored as integers and mapped to P{num:03d}.
    This is an approximation — see corpus_loader.MAHADEVAN_TO_PARPOLA for
    known divergences between the two numbering systems.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Corpus file not found: {filepath}\n"
            "Yadav et al. 2010 PLoS ONE dataset available on request from authors."
        )

    corpus = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text_id = row.get("id", "").strip()
            raw     = row.get("signs", "").replace(",", " ").strip()
            tokens  = [t.strip() for t in raw.split() if t.strip()]

            seq = []
            for t in tokens:
                if t.isdigit():
                    seq.append(f"P{int(t):03d}")
                else:
                    seq.append(t)

            if seq:
                corpus.append({"id": text_id, "site": row.get("site", "unknown"), "seq": seq})

    print(f"Loaded {len(corpus)} inscriptions from {filepath} (Yadav format)")
    return corpus


# ---------------------------------------------------------------------------
# Proof runner — runs proof 1 at multiple corpus scales and reports
# ---------------------------------------------------------------------------

def scale_proofs(external_corpus: list[dict] | None = None,
                 apply_mask: bool = True) -> dict:
    """
    Run Proof 1 (suffix theorem) at pilot scale and, if provided, at full scale.
    Erosion masking is applied automatically when apply_mask=True (default).

    This directly addresses the "small subcorpus" critique: if the p-value
    stays significant as corpus size grows, the critique is void. If it weakens,
    that is an honest finding to report.

    Returns dict with results at each scale tested.
    """
    from indus_decode import proof1_suffix_theorem

    results = {}

    # --- Pilot corpus (no erosion in hand-transcribed pilot; mask is a no-op) ---
    pilot_clean, pilot_mask_report = apply_erosion_mask(PILOT_CORPUS)
    pilot_result = proof1_suffix_theorem()
    results["pilot"] = {
        "n_seals":        len(PILOT_CORPUS),
        "n_clean":        len(pilot_clean),
        "p_value":        pilot_result["p_value"],
        "terminal_pct":   pilot_result["terminal_pct"],
        "label":          "PILOT (41 seals)",
        "erosion_masked": pilot_mask_report["dropped_count"],
        "verdict":        pilot_result["verdict"],
    }

    if external_corpus:
        import indus_decode as _id
        original = _id.CORPUS

        # Apply erosion mask to external corpus before running proofs
        if apply_mask:
            ext_clean, ext_mask_report = apply_erosion_mask(external_corpus)
            print(f"Erosion mask: dropped {ext_mask_report['dropped_count']} / "
                  f"{ext_mask_report['input_count']} inscriptions "
                  f"({ext_mask_report['drop_rate_pct']}%)")
        else:
            ext_clean, ext_mask_report = external_corpus, {"dropped_count": 0}

        _id.CORPUS = ext_clean
        try:
            ext_result = proof1_suffix_theorem()
        finally:
            _id.CORPUS = original

        results["full"] = {
            "n_seals":        len(external_corpus),
            "n_clean":        len(ext_clean),
            "p_value":        ext_result["p_value"],
            "terminal_pct":   ext_result["terminal_pct"],
            "label":          f"FULL ({len(ext_clean)} clean / {len(external_corpus)} total)",
            "erosion_masked": ext_mask_report["dropped_count"],
            "verdict":        ext_result["verdict"],
        }

        # Combined (pilot + deduplicated external, both masked)
        combined = pilot_clean + [
            s for s in ext_clean if s["id"] not in {x["id"] for x in PILOT_CORPUS}
        ]
        _id.CORPUS = combined
        try:
            comb_result = proof1_suffix_theorem()
        finally:
            _id.CORPUS = original

        results["combined"] = {
            "n_seals":      len(combined),
            "p_value":      comb_result["p_value"],
            "terminal_pct": comb_result["terminal_pct"],
            "label":        f"COMBINED ({len(combined)} seals)",
            "verdict":      comb_result["verdict"],
        }

    return results


def print_scale_report(results: dict) -> None:
    """Print a formatted comparison of proof results across corpus scales."""
    print("PROOF 1 (SUFFIX THEOREM) — CORPUS SCALE SENSITIVITY")
    print("=" * 60)
    print(f"  {'Scale':30} {'N seals':>8} {'Terminal%':>10} {'p-value':>14}")
    print("  " + "-" * 64)
    for key, r in results.items():
        print(f"  {r['label']:30} {r['n_seals']:>8} {r['terminal_pct']:>9.1f}% {r['p_value']:>14.2e}")
    print()
    if len(results) == 1:
        print("  NOTE: Only pilot corpus available. Provide an external corpus CSV")
        print("  to load_rao_csv() or load_yadav_csv() to run at full scale.")
        print()
        print("  Priority: obtain Yadav et al. 2010 (PLoS ONE) dataset (1,548 seals)")
        print("  or ICIT CSV export from Andreas Fuls (fuls@mailbox.tu-berlin.de).")


if __name__ == "__main__":
    results = scale_proofs()
    print_scale_report(results)
