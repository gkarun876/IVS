"""
Structural Substitution Synonym Extractor
==========================================
Finds signs that are mathematically forced synonyms by occupying the same
positional slot in structurally identical formulas across different sites.

No phonetics. No dictionaries. Pure structural cryptography.

Method:
  1. Take top 30 PMI pairs from mi_edges.csv
  2. For each sign in those pairs, find all inscriptions containing it
  3. Find structural substitutions: signs that swap into the same slot
     in sequences that are otherwise identical
  4. Geo-commodity test: signs concentrated >60% at one site

Output:
  results/v4/synonym_clusters.txt
  results/v4/geo_commodities.txt
"""

import json, csv, os
from collections import Counter, defaultdict

CORPUS_PATH   = "data/mahadevan_corpus.json"
MI_EDGES_PATH = "results/v4/mi_edges.csv"
RESULTS_DIR   = "results/v4"
TOP_PMI       = 30
GEO_THRESHOLD = 0.60
MIN_GEO_COUNT = 5


def load_corpus():
    with open(CORPUS_PATH) as f:
        data = json.load(f)
    for e in data:
        try:
            e["textnum"] = int(str(e["id"]).split("-")[0])
        except:
            e["textnum"] = None
    return data


def load_top_pmi(path, top_n):
    pairs = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append((int(row["sign_a"]), int(row["sign_b"]),
                          float(row["pmi_score"]), int(row["co_occurrence_count"])))
    pairs.sort(key=lambda x: -x[2])
    return pairs[:top_n]


def find_structural_substitutions(corpus):
    """
    For every pair of signs, check if they substitute into the same slot
    in sequences that are otherwise identical.

    A "structural substitution" is:
      seq1 = [A, X, B, C]
      seq2 = [A, Y, B, C]
    where X and Y are different signs in the same position, everything else equal.

    Returns list of (sign_x, sign_y, slot, shared_context, sites_x, sites_y)
    """
    # Build index: (tuple of seq with slot masked) -> list of (sign_at_slot, site, id)
    slot_index = defaultdict(list)

    for e in corpus:
        seq  = e["seq"]
        site = e.get("site", "unknown")
        eid  = e.get("id", "?")
        for i, sign in enumerate(seq):
            masked = tuple(seq[:i] + [-1] + seq[i+1:])  # -1 = masked slot
            slot_index[masked].append((sign, site, eid, i))

    # Find slots where multiple different signs appear
    substitutions = []
    for masked_seq, entries in slot_index.items():
        signs_in_slot = Counter(s for s, site, eid, pos in entries)
        if len(signs_in_slot) < 2:
            continue  # no substitution here

        # Get the two most common signs in this slot
        top_two = signs_in_slot.most_common(2)
        if top_two[0][1] < 2 or top_two[1][1] < 1:
            continue

        sign_x, cx = top_two[0]
        sign_y, cy = top_two[1]

        sites_x = [site for s, site, eid, pos in entries if s == sign_x]
        sites_y = [site for s, site, eid, pos in entries if s == sign_y]
        ids_x   = [eid  for s, site, eid, pos in entries if s == sign_x]
        ids_y   = [eid  for s, site, eid, pos in entries if s == sign_y]
        slot    = entries[0][3]

        context = list(masked_seq)
        substitutions.append({
            "sign_x":    sign_x,
            "sign_y":    sign_y,
            "count_x":   cx,
            "count_y":   cy,
            "slot":      slot,
            "seq_len":   len(masked_seq),
            "context":   context,
            "sites_x":   sites_x,
            "sites_y":   sites_y,
            "ids_x":     ids_x,
            "ids_y":     ids_y,
            "cross_site": bool(set(sites_x) & set(sites_y) == set() and
                               len(set(sites_x)) >= 1 and len(set(sites_y)) >= 1),
        })

    # Sort by: cross-site first, then by count
    substitutions.sort(key=lambda x: (-int(x["cross_site"]), -(x["count_x"]+x["count_y"])))
    return substitutions


def geo_commodity_test(corpus):
    """
    For every sign, calculate what % of its appearances come from one site.
    High concentration = possible regional commodity marker.
    """
    sign_sites = defaultdict(list)
    for e in corpus:
        site = e.get("site", "unknown")
        for sign in e["seq"]:
            sign_sites[sign].append(site)

    results = []
    for sign, sites in sign_sites.items():
        total = len(sites)
        if total < MIN_GEO_COUNT:
            continue
        top_site, top_n = Counter(sites).most_common(1)[0]
        concentration = top_n / total
        results.append({
            "sign":        sign,
            "total":       total,
            "top_site":    top_site,
            "top_site_n":  top_n,
            "concentration": round(concentration, 3),
        })

    results.sort(key=lambda x: -x["concentration"])
    return results


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    corpus = load_corpus()
    pairs  = load_top_pmi(MI_EDGES_PATH, TOP_PMI)

    pmi_signs = set()
    for a, b, pmi, cooc in pairs:
        pmi_signs.add(a)
        pmi_signs.add(b)
    print(f"Top {TOP_PMI} PMI pairs → {len(pmi_signs)} unique signs to analyse")

    # -----------------------------------------------------------------------
    # 1. Structural substitutions
    # -----------------------------------------------------------------------
    subs = find_structural_substitutions(corpus)

    out = ["=" * 68,
           "  STRUCTURAL SUBSTITUTION SYNONYMS",
           "  Pure structural cryptography — no phonetics, no dictionaries",
           "=" * 68]

    out.append(f"\nMethod: find signs that swap into the same slot in otherwise")
    out.append(f"identical sequences. Cross-site substitutions ranked first.")
    out.append(f"Total substitution patterns found: {len(subs)}")

    out.append(f"\n{'Rank':>4}  {'Sign_X':>7}  {'Sign_Y':>7}  {'Slot':>5}  "
               f"{'Cx':>4}  {'Cy':>4}  {'Cross-site':>10}  Context")
    out.append("  " + "-" * 80)

    shown = 0
    for r in subs:
        if shown >= 30:
            break
        ctx = str(r["context"]).replace("-1", "___")
        cross = "YES" if r["cross_site"] else "no"
        out.append(f"  {shown+1:>3}.  M{r['sign_x']:<5}  M{r['sign_y']:<5}  "
                   f"pos{r['slot']:>2}  {r['count_x']:>4}  {r['count_y']:>4}  "
                   f"{cross:>10}  {ctx}")
        if r["cross_site"]:
            sx = set(r["sites_x"])
            sy = set(r["sites_y"])
            out.append(f"         X sites: {sorted(sx)}")
            out.append(f"         Y sites: {sorted(sy)}")
        shown += 1

    # Highlight M267 vs M263 (our known case)
    known = [r for r in subs if
             (r["sign_x"] in (267,263) and r["sign_y"] in (267,263))]
    if known:
        out.append(f"\nKNOWN CASE CONFIRMED: M267 ↔ M263")
        r = known[0]
        out.append(f"  Slot {r['slot']} in {r['context']}")
        out.append(f"  M267 sites: {set(r['sites_x'])}  M263 sites: {set(r['sites_y'])}")

    # -----------------------------------------------------------------------
    # 2. Geo-commodity test
    # -----------------------------------------------------------------------
    geo = geo_commodity_test(corpus)

    out.append(f"\n{'='*68}")
    out.append(f"  GEO-COMMODITY TEST")
    out.append(f"  Signs with >60% appearances concentrated at one site")
    out.append(f"  (possible regional trade goods — NOT city names)")
    out.append(f"{'='*68}")
    out.append(f"\n  {'Sign':>6}  {'Total':>6}  {'Top Site':25}  {'Site_N':>6}  {'Concentration':>13}")
    out.append("  " + "-" * 66)

    count = 0
    for r in geo:
        if r["concentration"] < GEO_THRESHOLD:
            break
        if count >= 25:
            break
        out.append(f"  M{r['sign']:<5}  {r['total']:>6}  {r['top_site']:25}  "
                   f"{r['top_site_n']:>6}  {r['concentration']*100:>12.1f}%")
        count += 1

    result = "\n".join(out)
    print(result)

    path = os.path.join(RESULTS_DIR, "synonym_clusters.txt")
    with open(path, "w") as f:
        f.write(result)
    print(f"\nSaved → {path}")


if __name__ == "__main__":
    main()
