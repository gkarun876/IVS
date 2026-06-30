"""
Mutual Information Network — Undirected Co-occurrence Graph
===========================================================
Builds an undirected network of Indus signs based on Pointwise Mutual
Information (PMI) within inscriptions.

Unlike the bigram transition matrix (which is directional: A→B),
this graph asks only: do A and B appear on the same seal more often
than chance would predict?

High-degree nodes (hubs)  = signs that co-occur with many others
                          = candidates for grammatical function words
Low-degree nodes (leaves) = signs that co-occur with only 1-2 partners
                          = candidates for specialized content vocabulary

NO phonetic assumptions. NO directionality. Pure co-occurrence math.

Outputs:
  results/v4/mi_edges.csv           — all PMI-positive edges (A, B, PMI, count)
  results/v4/network_centrality.csv — per-sign degree + betweenness centrality
  results/v4/network_graph.graphml  — full graph for Gephi visualization
  results/v4/network_summary.txt    — top hubs, top leaves, interpretation
"""

import json
import csv
import os
import math
from collections import Counter, defaultdict
import networkx as nx

CORPUS_PATH = "data/mahadevan_corpus.json"
RESULTS_DIR = "results/v4"
MIN_COOC    = 3   # minimum co-occurrences to include an edge


def load_corpus(path):
    with open(path) as f:
        return json.load(f)


def compute_pmi(corpus):
    """
    Compute PMI for all sign pairs that co-occur in >= MIN_COOC inscriptions.

    p(A)   = inscriptions containing A / total inscriptions
    p(B)   = inscriptions containing B / total inscriptions
    p(A,B) = inscriptions containing both A and B / total inscriptions
    PMI    = log2(p(A,B) / (p(A) * p(B)))

    Negative PMI (signs avoid each other) set to 0 — we model attraction only.
    """
    n = len(corpus)

    # Sign unigram counts (inscription-level presence, not token count)
    sign_docs = Counter()
    pair_docs = Counter()
    sign_freq = Counter()   # total token frequency

    for entry in corpus:
        signs_in_doc = set(entry["seq"])   # unique signs per inscription
        sign_docs.update(signs_in_doc)
        sign_freq.update(entry["seq"])     # total tokens

        signs_list = sorted(signs_in_doc)
        for i in range(len(signs_list)):
            for j in range(i + 1, len(signs_list)):
                pair_docs[(signs_list[i], signs_list[j])] += 1

    pmi_edges = []
    for (a, b), cooc_count in pair_docs.items():
        if cooc_count < MIN_COOC:
            continue
        p_a   = sign_docs[a] / n
        p_b   = sign_docs[b] / n
        p_ab  = cooc_count   / n
        pmi   = math.log2(p_ab / (p_a * p_b))
        if pmi > 0:
            pmi_edges.append((a, b, round(pmi, 6), cooc_count))

    return pmi_edges, sign_docs, sign_freq


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    corpus = load_corpus(CORPUS_PATH)
    n      = len(corpus)
    print(f"Corpus: {n} inscriptions")

    pmi_edges, sign_docs, sign_freq = compute_pmi(corpus)
    print(f"PMI-positive edges (>= {MIN_COOC} co-occurrences): {len(pmi_edges)}")

    # -------------------------------------------------------------------------
    # 1. Save edges CSV
    # -------------------------------------------------------------------------
    edges_path = os.path.join(RESULTS_DIR, "mi_edges.csv")
    with open(edges_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sign_a", "sign_b", "pmi_score", "co_occurrence_count"])
        for a, b, pmi, cnt in sorted(pmi_edges, key=lambda x: -x[2]):
            writer.writerow([a, b, pmi, cnt])
    print(f"Saved → {edges_path}")

    # -------------------------------------------------------------------------
    # 2. Build NetworkX graph
    # -------------------------------------------------------------------------
    G = nx.Graph()

    for entry in corpus:
        for sign in set(entry["seq"]):
            if not G.has_node(sign):
                G.add_node(sign,
                           total_count=sign_freq[sign],
                           doc_count=sign_docs[sign])

    for a, b, pmi, cnt in pmi_edges:
        G.add_edge(a, b, weight=pmi, co_occurrence_count=cnt)

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # -------------------------------------------------------------------------
    # 3. Centrality measures
    # -------------------------------------------------------------------------
    print("Computing degree centrality...")
    deg_cent = nx.degree_centrality(G)

    print("Computing betweenness centrality...")
    bet_cent = nx.betweenness_centrality(G, weight="weight", normalized=True)

    centrality_path = os.path.join(RESULTS_DIR, "network_centrality.csv")
    with open(centrality_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sign", "degree", "degree_centrality",
                         "betweenness_centrality", "total_count", "doc_count"])
        for sign in sorted(G.nodes()):
            writer.writerow([
                sign,
                G.degree(sign),
                round(deg_cent[sign], 6),
                round(bet_cent[sign], 6),
                sign_freq[sign],
                sign_docs[sign],
            ])
    print(f"Saved → {centrality_path}")

    # -------------------------------------------------------------------------
    # 4. Export GraphML for Gephi
    # -------------------------------------------------------------------------
    graphml_path = os.path.join(RESULTS_DIR, "network_graph.graphml")
    nx.write_graphml(G, graphml_path)
    print(f"Saved → {graphml_path}")

    # -------------------------------------------------------------------------
    # 5. Summary report
    # -------------------------------------------------------------------------
    sorted_by_degree = sorted(deg_cent.items(), key=lambda x: -x[1])
    sorted_by_between = sorted(bet_cent.items(), key=lambda x: -x[1])

    # Leaves = degree 1 or 2
    leaves = [(s, G.degree(s)) for s in G.nodes() if G.degree(s) <= 2]
    leaves.sort(key=lambda x: x[1])

    out = []
    out.append("=" * 65)
    out.append("  MUTUAL INFORMATION NETWORK — SEMANTIC ARCHITECTURE")
    out.append(f"  Corpus: {n} inscriptions")
    out.append(f"  Graph:  {G.number_of_nodes()} signs (nodes), "
               f"{G.number_of_edges()} MI edges")
    out.append(f"  Min co-occurrence threshold: {MIN_COOC} inscriptions")
    out.append("=" * 65)

    out.append("")
    out.append("TOP 10 HUBS — highest degree centrality")
    out.append("  (appear with most different signs = likely grammatical function words)")
    out.append(f"  {'Sign':>6}  {'Degree':>7}  {'DegCent':>9}  {'BetCent':>9}  "
               f"{'TokFreq':>8}  {'DocFreq':>8}")
    out.append("  " + "-" * 60)
    for sign, dc in sorted_by_degree[:10]:
        out.append(f"  M{sign:<5}  {G.degree(sign):>7}  {dc:>9.4f}  "
                   f"{bet_cent[sign]:>9.4f}  "
                   f"{sign_freq[sign]:>8}  {sign_docs[sign]:>8}")

    out.append("")
    out.append("TOP 10 BRIDGES — highest betweenness centrality")
    out.append("  (connect different clusters = likely infixes or medial connectors)")
    out.append(f"  {'Sign':>6}  {'Degree':>7}  {'DegCent':>9}  {'BetCent':>9}  "
               f"{'TokFreq':>8}  {'DocFreq':>8}")
    out.append("  " + "-" * 60)
    for sign, bc in sorted_by_between[:10]:
        out.append(f"  M{sign:<5}  {G.degree(sign):>7}  {deg_cent[sign]:>9.4f}  "
                   f"{bc:>9.4f}  "
                   f"{sign_freq[sign]:>8}  {sign_docs[sign]:>8}")

    out.append("")
    out.append(f"TOP 10 LEAVES — degree 1 or 2 (n={len(leaves)} total leaves)")
    out.append("  (appear with only 1-2 partners = likely specialized content vocabulary)")
    out.append(f"  {'Sign':>6}  {'Degree':>7}  {'TokFreq':>8}  {'DocFreq':>8}")
    out.append("  " + "-" * 38)
    for sign, deg in leaves[:10]:
        out.append(f"  M{sign:<5}  {deg:>7}  {sign_freq[sign]:>8}  {sign_docs[sign]:>8}")

    out.append("")
    out.append("NETWORK TOPOLOGY SUMMARY")
    degrees = [G.degree(n) for n in G.nodes()]
    avg_deg = sum(degrees) / len(degrees) if degrees else 0
    out.append(f"  Average degree:       {avg_deg:.2f}")
    out.append(f"  Max degree:           {max(degrees)}")
    out.append(f"  Isolated nodes:       "
               f"{sum(1 for d in degrees if d == 0)}")
    out.append(f"  Leaf nodes (deg≤2):   {len(leaves)}")
    out.append(f"  Hub nodes (deg≥20):   "
               f"{sum(1 for d in degrees if d >= 20)}")

    components = list(nx.connected_components(G))
    out.append(f"  Connected components: {len(components)}")
    out.append(f"  Largest component:    {max(len(c) for c in components)} signs")

    out.append("")
    out.append("TOP 10 STRONGEST PMI PAIRS (highest mutual attraction)")
    out.append(f"  {'Sign A':>7}  {'Sign B':>7}  {'PMI':>8}  {'CoOcc':>6}")
    out.append("  " + "-" * 36)
    for a, b, pmi, cnt in sorted(pmi_edges, key=lambda x: -x[2])[:10]:
        out.append(f"  M{a:<6}  M{b:<6}  {pmi:>8.4f}  {cnt:>6}")

    result = "\n".join(out)
    print("\n" + result)

    summary_path = os.path.join(RESULTS_DIR, "network_summary.txt")
    with open(summary_path, "w") as f:
        f.write(result)
    print(f"\nSaved → {summary_path}")


if __name__ == "__main__":
    main()
