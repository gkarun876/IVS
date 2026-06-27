"""
ICIT Corpus Loader — Wells/Fuls Sign System Bridge
====================================================
Converts between the ICIT sign notation (Wells 3-digit codes) and the
Parpola sign notation (P-numbers) used throughout this framework.

Wells notation:  3-digit integers, e.g. 520, 740, 033
Parpola notation: P-prefix + 3-digit integer, e.g. P385, P122

ICIT search syntax (from Fuls 2010 documentation):
  - Signs separated by hyphens: 033-705-520
  - + marks text boundary: +520-033-705+
  - % is wildcard (any length): %TMK
  - _ is wildcard (one sign):   ___
  - Function codes: TMK, ITM, NUM, SYL, LOG

Sign function codes (ICIT):
  TMK  Terminal Marker
  ITM  Initial Cluster Terminal Marker
  LOG  Logogram
  NUM  Numeral
  SYL  Syllable

Sources:
  Wells, B. (2006). Epigraphic Approaches to Indus Writing. Harvard.
  Fuls, A. (2010). Online Indus Writing Database. indus.epigraphica.de
  Parpola, A. (1994). Deciphering the Indus Script. Cambridge.
  Mahadevan, I. (1977). The Indus Script: Text, Concordance and Tables.
"""

# ---------------------------------------------------------------------------
# Wells ↔ Parpola sign mapping
# Sources: Parpola 1994 Table 14; Wells 2006 Appendix; Mahadevan 1977
# Notes:
#   520, 740 — confirmed TMK (Terminal Marker) in Fuls 2010 examples
#   Both map to P385 (jar/vessel sign) in Parpola notation
#   060 — confirmed ITM (Initial Cluster Terminal Marker) in Fuls examples
# ---------------------------------------------------------------------------

WELLS_TO_PARPOLA = {
    # Terminal markers
    "520": "P385",   # jar sign — primary TMK (Fuls 2010 examples)
    "740": "P385",   # jar variant — secondary TMK (Fuls 2010 examples)

    # High-frequency signs (from Fuls cluster examples)
    "033": "P122",   # fish sign (meen)
    "705": "P316",   # vel / spear sign
    "060": "P060",   # ko / lord — confirmed ITM
    "220": "P062",   # malai / mountain
    "002": "P091",   # aaru / six-strokes
    "700": "P311",   # kudam / jar body
    "415": "P117",   # maram / tree
    "803": "P210",   # kai / hand
    "585": "P268",   # kodu / horn
    "760": "P324",   # punitam / sacred marker
    "817": "P174",   # ilai / leaf
    "861": "P175",   # poo / flower
    "920": "P352",   # vaal / sword-tail
    "853": "P210",   # kai variant
}

PARPOLA_TO_WELLS = {v: k for k, v in WELLS_TO_PARPOLA.items()}

# ICIT sign function codes
SIGN_FUNCTIONS = {
    "TMK": "Terminal Marker",
    "ITM": "Initial Cluster Terminal Marker",
    "LOG": "Logogram",
    "NUM": "Numeral",
    "LON": "Long Numeral",
    "SHN": "Short Numeral",
    "SSN": "Short Stacked Numeral",
    "SPN": "Special Numeral",
    "MIN": "Minas",
    "SYL": "Syllable",
    "PTM": "Post Terminal Marker",
    "XXX": "Test function",
}


# ---------------------------------------------------------------------------
# Parsers for ICIT text output formats
# ---------------------------------------------------------------------------

def parse_icit_textcode(textcode: str) -> list[str]:
    """
    Parse an ICIT textcode string into a list of Parpola sign IDs.

    ICIT format:  +520-033-705-220-002+
    Returns:      ['P385', 'P122', 'P316', 'P062', 'P091']

    Signs marked with + (text boundaries) are included.
    Unknown signs (000 = eroded) are preserved as 'P000'.
    Function codes (TMK, NUM, etc.) are resolved to their sign type label.
    """
    cleaned = textcode.strip().replace("+", "-").strip("-")
    tokens  = [t.strip() for t in cleaned.split("-") if t.strip()]

    result = []
    for token in tokens:
        if token in SIGN_FUNCTIONS:
            result.append(f"FUNC:{token}")
        elif token == "000":
            result.append("P000")   # eroded/unknown sign
        elif token.isdigit():
            result.append(WELLS_TO_PARPOLA.get(token, f"W{token}"))
        else:
            result.append(token)
    return result


def parse_icit_csv(filepath: str) -> list[dict]:
    """
    Parse a CSV export from the ICIT database into corpus format.

    Expected columns (ICIT text export):
        ICIT_ID, site, type, sign_code

    Returns list of dicts compatible with indus_decode.CORPUS format:
        [{"id": "1202", "site": "Mohenjo-daro", "seq": ["P385", "P122", ...]}, ...]
    """
    import csv

    corpus = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            icit_id   = row.get("ICIT_ID", row.get("id", "")).strip()
            site      = row.get("site", "").strip()
            sign_code = row.get("sign_code", row.get("text_code", "")).strip()

            if not sign_code:
                continue

            seq = parse_icit_textcode(sign_code)
            if seq:
                corpus.append({"id": icit_id, "site": site, "seq": seq})

    return corpus


def parse_icit_textlines(raw_text: str) -> list[dict]:
    """
    Parse copy-pasted text output from the ICIT web interface.

    Each line is expected to contain an ICIT ID and a sign code, e.g.:
        1202  Mohenjo-daro  SEAL:S  +520-033-705-220+
        1254  Mohenjo-daro  TAB:B   +740-760-033-705-803+

    Returns corpus-format list.
    """
    import re

    corpus = []
    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # Extract textcode — anything matching the +NNN-NNN+ pattern
        match = re.search(r'(\+[\d\-+]+\+)', line)
        if not match:
            continue

        textcode = match.group(1)
        parts    = line.split()
        icit_id  = parts[0] if parts else "?"
        site     = parts[1] if len(parts) > 1 else "unknown"
        seq      = parse_icit_textcode(textcode)

        corpus.append({"id": icit_id, "site": site, "seq": seq})

    return corpus


# ---------------------------------------------------------------------------
# Corpus merger — combine pilot corpus with ICIT data
# ---------------------------------------------------------------------------

def merge_with_pilot(icit_corpus: list[dict]) -> list[dict]:
    """
    Merge ICIT corpus with the pilot corpus from indus_decode.py,
    deduplicating by seal ID.
    """
    from indus_decode import CORPUS as PILOT

    merged = {s["id"]: s for s in PILOT}
    for seal in icit_corpus:
        if seal["id"] not in merged:
            merged[seal["id"]] = seal

    result = list(merged.values())
    print(f"Merged corpus: {len(PILOT)} pilot + "
          f"{len(icit_corpus)} ICIT = {len(result)} total (deduplicated)")
    return result


# ---------------------------------------------------------------------------
# ICIT query builder — generates search strings for the web interface
# ---------------------------------------------------------------------------

def build_query(signs: list[str], position: str = "any") -> str:
    """
    Build an ICIT search string from a list of Parpola sign IDs.

    position options:
      'any'      — signs appear anywhere: %-033-%
      'terminal' — signs appear at end:   %-033+
      'initial'  — signs appear at start: +033-%

    Example:
      build_query(['P122', 'P385'], 'terminal')
      → '%-033-520+'
    """
    wells = []
    for p in signs:
        w = PARPOLA_TO_WELLS.get(p)
        if w:
            wells.append(w)
        else:
            wells.append("___")   # unknown mapping → wildcard

    code = "-".join(wells)

    if position == "terminal":
        return f"%-{code}+"
    elif position == "initial":
        return f"+{code}-%"
    else:
        return f"%-{code}-%"


# ---------------------------------------------------------------------------
# Quick-reference queries for ICIT web interface
# ---------------------------------------------------------------------------

USEFUL_QUERIES = {
    "All terminal marker texts":          "%TMK",
    "P385 (TMK) at terminal position":    "%+TMK+",
    "Fish sign (P122/033) anywhere":      "%033%",
    "Fish → terminal marker bigram":      "%-033-TMK+",
    "Murugan cluster (vel+fish+mountain)":"%-705%033%220%",
    "All texts from Mohenjo-daro":        "% (filter by site)",
    "Two-sign texts only":                "+___-___+",
    "Texts with numerals":                "%NUM%",
}


if __name__ == "__main__":
    print("ICIT CORPUS LOADER — SIGN BRIDGE")
    print("=" * 50)

    print("\nWells → Parpola mappings loaded:")
    for w, p in WELLS_TO_PARPOLA.items():
        print(f"  Wells {w}  →  {p}")

    print("\nUseful ICIT search queries:")
    for desc, query in USEFUL_QUERIES.items():
        print(f"  {query:35s}  # {desc}")

    print("\nExample: parse ICIT textcode")
    sample = "+520-033-705-220-002+"
    parsed = parse_icit_textcode(sample)
    print(f"  Input:  {sample}")
    print(f"  Output: {parsed}")

    print("\nExample: build query for P122→P385 at terminal position")
    q = build_query(["P122", "P385"], position="terminal")
    print(f"  Query: {q}")
    print(f"  Paste this into ICIT search box to find all meen→-an terminal bigrams")
