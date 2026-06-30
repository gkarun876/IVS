"""
Motif Scraper — Pull fs80 field symbol codes from Firestore
============================================================
The indusscript.in Firestore database contains `fs80` (field symbol code)
for every inscription. We never captured this in the original scrape.

fs80 ranges (from IDF80 / Mahadevan field symbol classification):
  11-19   = UNICORN
  22-50   = BULL
  61-65   = BUFFALO
  71-82   = ELEPHANT
  91-104  = TIGER
  111-121 = RHINO
  131-139 = GOAT-ANTELOPE
  141-149 = OX-ANTELOPE
  150     = TWO GOATS
  163-171 = HARE
  181-221 = GROUP OF ANIMALS
  231-262 = FABULOUS ANIMAL
  361-431 = REPTILES / FISH / BIRDS
  660     = NO FIELD SYMBOL (text-only seal)
  0       = UNKNOWN / NOT SET

Usage:
  python scrape_motifs.py --token "eyJhbGci..."

Output:
  data/motif_data.json  — {textnum: {fs80: int, motif: str}}
"""

import json
import time
import argparse
import urllib.request
import urllib.parse

FIRESTORE_BASE = (
    "https://firestore.googleapis.com/v1/projects/theindusscript"
    "/databases/(default)/documents/indusarrays"
)

CORPUS_PATH = "data/mahadevan_corpus.json"
OUTPUT_PATH = "data/motif_data.json"

# fs80 → motif label (from indusscript.in FIELD SYMBOLS tab)
def fs80_to_motif(fs80: int) -> str:
    if fs80 == 0:
        return "UNKNOWN"
    elif 11 <= fs80 <= 19:
        return "UNICORN"
    elif 22 <= fs80 <= 50:
        return "BULL"
    elif 61 <= fs80 <= 65:
        return "BUFFALO"
    elif 71 <= fs80 <= 82:
        return "ELEPHANT"
    elif 91 <= fs80 <= 104:
        return "TIGER"
    elif 111 <= fs80 <= 121:
        return "RHINO"
    elif 131 <= fs80 <= 139:
        return "GOAT-ANTELOPE"
    elif 141 <= fs80 <= 149:
        return "OX-ANTELOPE"
    elif fs80 == 150:
        return "TWO-GOATS"
    elif 163 <= fs80 <= 171:
        return "HARE"
    elif 181 <= fs80 <= 221:
        return "GROUP-OF-ANIMALS"
    elif 231 <= fs80 <= 262:
        return "FABULOUS-ANIMAL"
    elif 361 <= fs80 <= 431:
        return "REPTILE-FISH-BIRD"
    elif fs80 == 660:
        return "NO-MOTIF"
    else:
        return f"OTHER-{fs80}"


def fetch_document(doc_index: int, token: str) -> dict | None:
    """
    Fetch a single indusarrays document by its Firestore index.
    Returns the fields dict or None on failure.
    """
    url = f"{FIRESTORE_BASE}/{doc_index}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("fields", {})
    except Exception:
        return None


def get_int_field(fields: dict, key: str) -> int | None:
    val = fields.get(key, {})
    if "integerValue" in val:
        return int(val["integerValue"])
    if "stringValue" in val:
        try:
            return int(val["stringValue"])
        except ValueError:
            return None
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Firebase Bearer token")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max documents to fetch (0 = all)")
    args = parser.parse_args()

    # Load corpus to get all textnum IDs
    with open(CORPUS_PATH) as f:
        corpus = json.load(f)

    # Build textnum -> corpus entry mapping
    # corpus IDs are strings like "1003", "1004a", etc.
    # textnum in Firestore is the numeric part
    textnum_set = set()
    for entry in corpus:
        try:
            textnum_set.add(int(str(entry["id"]).replace("a", "").replace("b", "")))
        except ValueError:
            pass

    print(f"Corpus: {len(corpus)} inscriptions, {len(textnum_set)} unique textnums")

    # We need to find which Firestore document index maps to each textnum.
    # From the scrape data: Firestore index != textnum directly.
    # We'll scan index range 1-5000 and match by textnum field.
    # Alternatively, query by textnum field using REST structured query.

    motif_data = {}
    errors = 0
    fetched = 0

    # Use Firestore REST structured query to find documents by textnum
    # Query: collection indusarrays where textnum IN [our textnums]
    # Firestore supports IN with up to 30 values — batch in chunks of 30

    textnums = sorted(textnum_set)
    if args.limit:
        textnums = textnums[:args.limit]

    print(f"Fetching fs80 for {len(textnums)} textnums...")

    QUERY_URL = (
        "https://firestore.googleapis.com/v1/projects/theindusscript"
        "/databases/(default)/documents:runQuery"
    )

    chunk_size = 30
    for i in range(0, len(textnums), chunk_size):
        chunk = textnums[i:i+chunk_size]

        query_body = {
            "structuredQuery": {
                "from": [{"collectionId": "indusarrays"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "textnum"},
                        "op": "IN",
                        "value": {
                            "arrayValue": {
                                "values": [{"integerValue": str(t)} for t in chunk]
                            }
                        }
                    }
                },
                "select": {
                    "fields": [
                        {"fieldPath": "textnum"},
                        {"fieldPath": "fs80"},
                        {"fieldPath": "posnum"},
                    ]
                },
                "limit": chunk_size * 5,
            }
        }

        body = json.dumps(query_body).encode("utf-8")
        req = urllib.request.Request(QUERY_URL, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {args.token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                results = json.loads(resp.read())

            for item in results:
                doc = item.get("document")
                if not doc:
                    continue
                fields = doc.get("fields", {})
                textnum = get_int_field(fields, "textnum")
                fs80    = get_int_field(fields, "fs80")
                posnum  = get_int_field(fields, "posnum")

                if textnum is None or fs80 is None:
                    continue

                # Only take posnum=1 (first line) to get the inscription-level motif
                # Multiple rows can share a textnum (multi-line inscriptions)
                if textnum not in motif_data or posnum == 1:
                    motif_data[textnum] = {
                        "fs80":  fs80,
                        "motif": fs80_to_motif(fs80),
                    }
                fetched += 1

        except Exception as e:
            errors += 1
            print(f"  Chunk {i//chunk_size} failed: {e}")
            time.sleep(1)

        if (i // chunk_size) % 10 == 0:
            print(f"  {i+len(chunk)}/{len(textnums)} textnums processed, "
                  f"{len(motif_data)} unique motifs so far...")
        time.sleep(0.05)   # gentle rate limit

    print(f"\nFetched: {fetched} rows → {len(motif_data)} unique textnums")
    print(f"Errors:  {errors} chunks failed")

    # Motif distribution
    from collections import Counter
    dist = Counter(v["motif"] for v in motif_data.values())
    print("\nMotif distribution:")
    for motif, cnt in dist.most_common():
        print(f"  {motif:25s}  {cnt:>4}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(motif_data, f, indent=2)
    print(f"\nSaved → {OUTPUT_PATH}  ({len(motif_data)} entries)")


if __name__ == "__main__":
    main()
