"""
Mahadevan Codebook
==================
Source: Mahadevan (1977) concordance table definitions.
These are the official code mappings for the motif data fields.

Field: textnum (inscription ID ranges → site)
Field: inscobj (object type code)
Field: sideline (side of object)
Field: fs80 (field symbol / motif code)
Field: posnum (line of text code)
Field: dir (direction of writing)
"""

# ---------------------------------------------------------------------------
# 1. TEXT NUMBER RANGES → SITE
# Source: Table 1 "CODE FOR TEXT NUMBERS"
# ---------------------------------------------------------------------------
TEXTNUM_SITE = [
    (1001, 1905, "Mohenjo-daro (MIC vol.III)"),
    (2002, 2952, "Mohenjo-daro (FEM vol.II)"),
    (3001, 3513, "Mohenjo-daro (Other texts)"),
    (4001, 4905, "Harappa (EH vol.II)"),
    (5001, 5601, "Harappa (Other texts)"),
    (6104, 6306, "Chanhudaro (CE)"),
    (6402, 6405, "Chanhudaro (Other texts)"),
    (7001, 7301, "Lothal"),
    (8001, 8302, "Kalibangan"),
    (9001, 9701, "Other Sites"),
    (9801, 9905, "West Asian Finds"),
]

def site_from_textnum(n: int) -> str:
    for lo, hi, site in TEXTNUM_SITE:
        if lo <= n <= hi:
            return site
    return "Unknown"


# ---------------------------------------------------------------------------
# 2. INSCOBJ → OBJECT TYPE
# Source: Table 2 "CODE FOR TYPES OF INSCRIBED OBJECTS" (Numerical col.5)
# ---------------------------------------------------------------------------
INSCOBJ = {
    "1": "Seals",
    "2": "Sealings",
    "3": "Miniature tablets (stone/terracotta/faience)",
    "4": "Pottery graffiti",
    "5": "Copper tablets",
    "6": "Bronze implements",
    "7": "Ivory or bone rods",
    "9": "Miscellaneous inscribed objects",
}

def inscobj_label(code: str) -> str:
    return INSCOBJ.get(str(code), f"Unknown-{code}")


# ---------------------------------------------------------------------------
# 3. SIDELINE → SIDE OF OBJECT
# Source: Table 3 "CODE FOR SIDES OF INSCRIBED OBJECTS" (Numerical col.6)
# ---------------------------------------------------------------------------
SIDELINE = {
    "0": "Only side",
    "1": "First side",
    "2": "Second side",
    "3": "Third side",
    "4": "Fourth side",
    "5": "Fifth side",
    "6": "Sixth side",
}

def sideline_label(code: str) -> str:
    return SIDELINE.get(str(code), f"Unknown-{code}")


# ---------------------------------------------------------------------------
# 4. FS80 (IDF80) → FIELD SYMBOL / MOTIF
# Source: Table 4 "CODE FOR FIELD SYMBOLS"
# IDF80 code ranges → Field Symbol Types
# fs80=0 = "No field symbol on the side" (FS77 code 0)
# fs80=660 observed = maps to 600-810 range = Scenes (anthropomorphic/animal)
# ---------------------------------------------------------------------------
FS80_RANGES = [
    (11,   352, "Animals"),
    (361,  431, "Reptiles, fish, birds etc"),
    (441,  460, "Trees and leaves"),
    (470,  599, "Anthropomorphic (divine, semi-divine or human) forms"),
    (600,  810, "Scenes with anthropomorphic and animal figures, trees and objects"),
    (821,  988, "Various symbols, motifs and geometrical patterns"),
    (999,  999, "Damaged or illegible field symbol"),
    (0,    0,   "No field symbol on the side"),
]

# Specific animal sub-ranges (from earlier screenshot)
ANIMAL_MOTIFS = {
    range(11,  20):  "UNICORN",
    range(22,  51):  "BULL",
    range(61,  66):  "BUFFALO",
    range(71,  83):  "ELEPHANT",
    range(91,  105): "TIGER",
    range(111, 122): "RHINO",
    range(131, 140): "GOAT-ANTELOPE",
    range(141, 150): "OX-ANTELOPE",
    range(150, 151): "TWO-GOATS",
    range(163, 172): "HARE",
    range(181, 222): "GROUP-OF-ANIMALS",
    range(231, 263): "FABULOUS-ANIMAL",
    range(361, 432): "REPTILE-FISH-BIRD",
}

def fs80_label(fs80: int) -> str:
    if fs80 == 0:
        return "NO-MOTIF"
    if fs80 == 999:
        return "DAMAGED"
    for r, label in ANIMAL_MOTIFS.items():
        if fs80 in r:
            return label
    for lo, hi, label in FS80_RANGES:
        if lo <= fs80 <= hi:
            return label.upper().replace(" ", "-").replace(",", "")[:20]
    return f"OTHER-{fs80}"


# ---------------------------------------------------------------------------
# 5. POSNUM (sideline = line of text)
# Source: Table 5 "CODE FOR LINES OF TEXT" (Numerical col.9)
# NOTE: The field is called `sideline` in the data but maps to line number
# ---------------------------------------------------------------------------
LINES_OF_TEXT = {
    "0": "Only line on side",
    "1": "First line",
    "2": "Second line",
    "3": "Third line",
    "9": "Side has field symbol only, no text",
}

def line_label(code: str) -> str:
    return LINES_OF_TEXT.get(str(code), f"Line-{code}")


# ---------------------------------------------------------------------------
# 6. DIR → DIRECTION OF WRITING
# Source: Table 6 "DIRECTION OF WRITING"
# Standard Mahadevan coding:
#   1 = Right to Left (RTL) — the dominant direction
#   2 = Left to Right (LTR)
#   3 = Boustrophedon (alternating)
#   4 = Uncertain
# ---------------------------------------------------------------------------
DIRECTION = {
    "1": "Right to left",
    "2": "Left to right",
    "3": "Single sign in the line of text",
    "4": "Symmetrical arrangement of signs",
    "5": "Doubtful (damaged or illegible signs)",
    "9": "No line of text",
    "0": "Unknown",
}

def dir_label(code: str) -> str:
    return DIRECTION.get(str(code), f"Unknown-{code}")


# ---------------------------------------------------------------------------
# 7. SITE LETTER CODES
# Source: Table 7 "LETTER CODE FOR SITES"
# ---------------------------------------------------------------------------
SITE_CODES = {
    "MD": "Mohenjodaro",
    "HP": "Harappa",
    "CD": "Chanhudaro",
    "LL": "Lothal",
    "KB": "Kalibangan",
    "OS": "Other Sites",
    "WA": "West Asian Finds",
}

def site_from_code(code: str) -> str:
    return SITE_CODES.get(str(code).upper(), f"Unknown-{code}")


# ---------------------------------------------------------------------------
# 8. CONVENTIONAL SYMBOLS
# Source: Table 8 "CONVENTIONAL SYMBOLS USED IN THE TABLES"
# ---------------------------------------------------------------------------
CONVENTIONAL_SYMBOLS = {
    "*": "Sign read doubtfully (asterisk prefixed to top right of sign)",
    "[]": "Illegible or lost passage with one or more signs",
}


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("CODEBOOK SELF-TEST")
    print("=" * 50)
    print(f"textnum 1006 → {site_from_textnum(1006)}")
    print(f"textnum 4034 → {site_from_textnum(4034)}")
    print(f"textnum 7001 → {site_from_textnum(7001)}")
    print()
    print(f"inscobj '1' → {inscobj_label('1')}")
    print(f"inscobj '2' → {inscobj_label('2')}")
    print(f"inscobj '4' → {inscobj_label('4')}")
    print()
    print(f"fs80 11  → {fs80_label(11)}")
    print(f"fs80 13  → {fs80_label(13)}")
    print(f"fs80 22  → {fs80_label(22)}")
    print(f"fs80 71  → {fs80_label(71)}")
    print(f"fs80 660 → {fs80_label(660)}")
    print(f"fs80 0   → {fs80_label(0)}")
    print()
    print(f"dir '1'  → {dir_label('1')}")
    print(f"dir '3'  → {dir_label('3')}")
    print(f"dir '4'  → {dir_label('4')}")
    print(f"dir '5'  → {dir_label('5')}")
    print(f"dir '9'  → {dir_label('9')}")
    print()
    print(f"sideline '0' → {sideline_label('0')}")
    print()
    print(f"site 'MD' → {site_from_code('MD')}")
    print(f"site 'HP' → {site_from_code('HP')}")
    print(f"site 'WA' → {site_from_code('WA')}")
