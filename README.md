# Indus Valley Script — Computational Statistical Analysis

An open-source, reproducible statistical framework for analysing the structural
properties of the Indus Valley Script (IVS). Built to survive peer review: every
claim is tagged `[SAFE]` (independently confirmed) or `[PREDICTED]` (testable
hypothesis), and every known limitation is explicitly documented.

**Paper:** `paper/main.tex` — *Statistical Evidence for Agglutinative Structure in
the Indus Valley Script: A Computational Analysis of 2,742 Inscriptions*

---

## What This Is

We do not claim to decipher the script. We ask: *if the script encodes language,
what structural properties does that language have?*

Nine independently falsifiable statistical tests on a corpus of **N = 2,742 clean
inscriptions** (Mahadevan 1977 concordance, textnums 1001–9905, Mohenjo-daro through
West Asian finds) answer this question without any phonetic assumptions.

---

## Repository Structure

```
# Core pipeline — full corpus (N = 2,742)
run_proofs_v2.py             — Proofs 1–4 (suffix, entropy, cluster, agglutination)
grammar_engine.py            — Proof 5 (bigram transition matrix, functional classes)
validation_mark_test.py      — Proof 6 (cross-site Markov consistency)
direction_grammar_test.py    — Proof 7 (RTL vs LTR direction grammar test)
motif_correlation.py         — Motif–sign correlation (M113 elephant, M172-M304 Kalibangan)
synonym_extractor.py         — Geographic sign clusters + structural substitution synonyms
mi_network.py                — PMI co-occurrence network (produces results/v4/mi_edges.csv)

phonetic_anchors.py          — DEDR phonetic bridge ([SAFE] / [PREDICTED] labels)

# Data
data/mahadevan_corpus.json   — 2,742 clean inscriptions (pre-parsed, included)
data/motif_data.json         — 3,916 motif records (fs80, dir, inscobj per textnum)
data/codebook.py             — Mahadevan codebook: fs80 → motif, dir → direction, etc.

# Results
results/v4/mi_edges.csv             — PMI network edges (required by motif_correlation.py
                                      and synonym_extractor.py)
results/v4/direction_grammar_test.txt
results/v4/motif_lexicon.txt
results/v4/motif_summary.txt
results/v4/synonym_clusters.txt

# Paper
paper/main.tex               — LaTeX source (24 pages)
paper/fig1_entropy.pdf       — Positional entropy profile (Figure 1)
paper/fig2_gradient.pdf      — Geographic grammar gradient (Figure 2)
paper/make_figures.py        — Generates both figures from corpus data
paper/references.bib         — Bibliography
```

---

## Nine Statistical Tests

All tests use Mahadevan (1977) sign numbering (M1–M417).

| # | Test | Key Result |
|---|------|-----------|
| 1 | **Suffix Theorem** | M342 terminal 68.0%, p = 1.70×10⁻²²² |
| 2 | **Positional Entropy** | −0.558 bits drop pos 0→1 |
| 3 | **Co-occurrence Cluster** | M267+M99+M342 at 5.5×, χ²=523, p≈0 |
| 4 | **Agglutination Ratio** | M48→M342 at 8.97× above independence |
| 5 | **Grammar Engine** | 398 signs, 598 transitions, 3 functional classes |
| 6 | **Cross-Site Markov** | Z=50.12, p=0; grammar decays with geographic distance |
| 7 | **Direction Grammar** | LTR 7,887× below random, p=1.03×10⁻⁵⁴; RTL limitation resolved |
| 8 | **Motif Correlation** | M113 at 37.9× on elephant seals; M172-M304 frozen Kalibangan formula |
| 9 | **Geographic Clusters** | M328=90.1% Harappa, M93=100% Chanhudaro; 154 structural synonyms |

---

## Quick Start

```bash
pip install -r requirements.txt

# data/mahadevan_corpus.json is pre-parsed and included in the repo

# Run all 9 tests
python run_proofs_v2.py              # Proofs 1-4, results/v2/
python grammar_engine.py             # Proof 5, grammar_summary.txt
python validation_mark_test.py       # Proof 6, cross_site_*.txt
python direction_grammar_test.py     # Proof 7, results/v4/direction_grammar_test.txt
python motif_correlation.py          # Proof 8, results/v4/motif_summary.txt
python synonym_extractor.py          # Proof 9, results/v4/synonym_clusters.txt

# Generate paper figures
cd paper && python make_figures.py   # fig1_entropy.pdf, fig2_gradient.pdf

# Compile paper
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

**Note:** `motif_correlation.py` and `synonym_extractor.py` require
`results/v4/mi_edges.csv` (produced by `mi_network.py`). This file is
included in the repository.

---

## Phonetic Anchors

Phonetic readings are isolated and do not affect any structural result.
Every reading carries an explicit confidence label.

| Sign | IAST | Meaning | DEDR | Confidence |
|------|------|---------|------|-----------|
| M342 | *-aṇ* | masc. nominal suffix | Krishnamurti 2003 §3.5 | `[SAFE]` |
| M149 | *mīn* | fish / star | DEDR-4889 | `[SAFE]` |
| M316 | *vēl* | spear | DEDR-5541 | `[SAFE]` |
| M60  | *kō* | king / lord | DEDR-2178 | `[SAFE]` |
| M62  | *malai* | mountain | DEDR-4710 | `[SAFE]` |
| M91  | *āru* | six / river | DEDR-338 | `[SAFE]` |

`[SAFE]` = confirmed in Parpola (1994), Mahadevan (1977), or DEDR (Burrow & Emeneau 1984).
`[PREDICTED]` = testable hypothesis; none currently listed.

---

## Archaeological Validation

**Rajan & Sivanantham (2025).** *Indus Signs and Graffiti Marks of Tamil Nadu:
A Morphological Study.* Dept. of Archaeology, Govt. of Tamil Nadu. Pub. No. 357.

- 14,165 graffiti-bearing sherds from 140 Tamil Nadu sites
- Signs M304 (Rajan sign 31.0) and M328 (Rajan sign 32.0) — independently
  isolated by our PMI/positional algorithms as highly localized markers —
  confirmed as exact shape-matches in Tamil Nadu Iron Age graffiti
- This is morphological corroboration only; no phonetic inference follows

---

## Known Limitations

| Limitation | Status |
|-----------|--------|
| RTL direction assumption | **RESOLVED** — direction field from motif_data.json; 86.1% RTL confirmed; LTR 7,887× below random under RTL grammar |
| Erosion bias | 703 inscriptions dropped; clean corpus skews slightly toward longer texts |
| West Asian sample size | n=13; geographic gradient finding robust at all other sites |
| No bilingual anchor | Phonetic readings probabilistic; none confirmed from bilingual text |
| Temporal gap (IVC → Keeladi: 1,300 yr) | Acknowledged; BRW tradition as bridge; transition probability verification pending |

---

## Corpus

**Source:** Mahadevan (1977) concordance.
Textnums 1001–9905 covering Mohenjo-daro, Harappa, Chanhudaro, Lothal,
Kalibangan, Other Sites, and West Asian finds.

| Site | Inscriptions |
|------|-------------|
| Mohenjo-daro | 1,347 |
| Harappa | 1,103 |
| Lothal | 112 |
| Kalibangan | 80 |
| Chanhudaro | 58 |
| Other Sites | 29 |
| West Asian | 13 |
| **Total** | **2,742** |

---

## License

MIT
