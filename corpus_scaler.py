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
from indus_decode import CORPUS as PILOT_CORPUS, proof1_suffix_theorem


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

def scale_proofs(external_corpus: list[dict] | None = None) -> dict:
    """
    Run Proof 1 (suffix theorem) at pilot scale and, if provided, at full scale.

    This directly addresses the "small subcorpus" critique: if the p-value
    stays significant as corpus size grows, the critique is void. If it weakens,
    that is an honest finding to report.

    Returns dict with results at each scale tested.
    """
    from indus_decode import proof1_suffix_theorem

    results = {}

    # --- Pilot corpus ---
    pilot_result = proof1_suffix_theorem()
    results["pilot"] = {
        "n_seals":        len(PILOT_CORPUS),
        "p_value":        pilot_result["p_value"],
        "terminal_pct":   pilot_result["terminal_pct"],
        "label":          "PILOT (41 seals)",
        "verdict":        pilot_result["verdict"],
    }

    if external_corpus:
        # Monkey-patch CORPUS and re-run proof 1
        import indus_decode as _id
        original = _id.CORPUS
        _id.CORPUS = external_corpus
        try:
            ext_result = proof1_suffix_theorem()
        finally:
            _id.CORPUS = original

        results["full"] = {
            "n_seals":      len(external_corpus),
            "p_value":      ext_result["p_value"],
            "terminal_pct": ext_result["terminal_pct"],
            "label":        f"FULL ({len(external_corpus)} seals)",
            "verdict":      ext_result["verdict"],
        }

        # Combined
        combined = PILOT_CORPUS + [
            s for s in external_corpus if s["id"] not in {x["id"] for x in PILOT_CORPUS}
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
