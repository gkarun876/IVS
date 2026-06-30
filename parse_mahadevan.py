"""
NOTE: Hardcoded input path is /root/.claude/uploads/indusarray_raw.txt — change
before re-running. Output is data/mahadevan_corpus.json (already committed).
This script need only be re-run if the raw Firestore dump is re-scraped.
----------------------------------------------------------------------
Mahadevan corpus parser — indusarray_raw.txt → clean corpus JSON
================================================================
Input format (tab-separated):
    textnum  sideline  sign1 sign2 ... signN

sideline encoding:
    side = sideline // 10   (0 = only side)
    line = sideline % 10    (0 = only line, 1 = first line, 2 = second, ...)

Sign conventions:
    *NNN  = doubtful reading — asterisk stripped, number kept
    0     = illegible/eroded gap — kept as token 0 for erosion mask

Direction assumption:
    All inscriptions assumed RTL (right-to-left), the standard for IVC seals.
    KNOWN LIMITATION: ~5% of inscriptions (LTR tablets/graffiti) will have
    reversed sign order. dir field not captured in raw export.

Erosion mask:
    Inscriptions containing sign 0 (illegible gap) are dropped before output.
"""

import json
import sys
from collections import defaultdict

SITE_MAP = [
    (1001, 3513, "Mohenjo-daro"),
    (4001, 5601, "Harappa"),
    (6104, 6405, "Chanhudaro"),
    (7001, 7301, "Lothal"),
    (8001, 8302, "Kalibangan"),
    (9001, 9701, "Other Sites"),
    (9801, 9905, "West Asian"),
]

def site_from_textnum(n: int) -> str:
    for lo, hi, name in SITE_MAP:
        if lo <= n <= hi:
            return name
    return "Unknown"


def parse_sign(token: str) -> int:
    """Strip * prefix and return integer sign number."""
    return int(token.lstrip("*"))


def load_raw(filepath: str) -> list[dict]:
    """
    Parse indusarray_raw.txt into corpus format.

    Returns list of dicts:
        {"id": "1001", "site": "Mohenjo-daro", "seq": [67, 72, 8, 342]}

    Multi-side inscriptions become separate entries:
        {"id": "1018-A", ...}  (side 1)
        {"id": "1018-B", ...}  (side 2)
    """
    # group rows by (textnum, side)
    # key → sorted list of (line, [signs])
    groups: dict[tuple, list] = defaultdict(list)

    with open(filepath, encoding="utf-8") as f:
        for raw_line in f:
            raw_line = raw_line.rstrip("\n")
            if not raw_line.strip():
                continue

            parts = raw_line.split("\t")
            if len(parts) < 3:
                continue

            textnum   = int(parts[0])
            sideline  = int(parts[1])
            sign_toks = parts[2].split()

            side = sideline // 10
            line = sideline % 10

            signs = [parse_sign(t) for t in sign_toks if t]
            groups[(textnum, side)].append((line, signs))

    # merge lines within each (textnum, side) group
    SIDE_LABELS = {0: "", 1: "-A", 2: "-B", 3: "-C", 4: "-D", 5: "-E", 6: "-F"}

    corpus = []
    for (textnum, side), line_list in sorted(groups.items()):
        # sort by line number so lines concatenate in order
        line_list.sort(key=lambda x: x[0])
        merged = []
        for _, signs in line_list:
            merged.extend(signs)

        label = SIDE_LABELS.get(side, f"-S{side}")
        entry_id = str(textnum) + label
        site = site_from_textnum(textnum)

        corpus.append({"id": entry_id, "site": site, "seq": merged})

    return corpus


def apply_erosion_mask(corpus: list[dict]) -> tuple[list[dict], int]:
    """Drop any inscription whose sequence contains sign 0 (illegible gap)."""
    clean = [e for e in corpus if 0 not in e["seq"]]
    dropped = len(corpus) - len(clean)
    return clean, dropped


def main(filepath: str, out_json: str):
    raw = load_raw(filepath)
    print(f"Loaded   {len(raw):>5} inscription-sides")

    clean, dropped = apply_erosion_mask(raw)
    print(f"Dropped  {dropped:>5} (contain illegible gap sign 0)")
    print(f"Clean    {len(clean):>5} inscriptions for analysis")

    sites = {}
    for e in clean:
        sites[e["site"]] = sites.get(e["site"], 0) + 1
    print("\nSite distribution:")
    for site, count in sorted(sites.items(), key=lambda x: -x[1]):
        print(f"  {site:<20} {count}")

    # sign frequency check
    from collections import Counter
    freq = Counter()
    for e in clean:
        freq.update(e["seq"])
    terminal = 342
    print(f"\nSign 342 frequency: {freq[terminal]} occurrences across {len(clean)} inscriptions")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(clean, f)
    print(f"\nSaved → {out_json}")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "/root/.claude/uploads/e07edfb8-f0aa-59ff-b7df-658f0b470c6b/aa42918c-indusarray_raw.txt"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/mahadevan_corpus.json"

    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    main(inp, out)
