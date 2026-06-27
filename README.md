# Indus Valley Script — Proto-Dravidian Decipherment Framework

An open-source, reproducible statistical framework for testing the Proto-Dravidian (Tamil) hypothesis for the Indus Valley Script.

---

## Hypothesis

The Indus Valley Script (c. 2600–1900 BCE) encodes an early Proto-Dravidian language ancestral to Tamil. This is the strongest current hypothesis in the field, supported by converging lines of evidence:

- Rao et al. (2009, *Science*) — conditional entropy of the corpus matches natural languages, not random symbol systems
- Parpola (1994) — systematic rebus analysis linking Indus pictograms to Dravidian homophones across 60 years of fieldwork
- Mahadevan (1977, 2014) — concordance of 3,700+ inscriptions demonstrating consistent positional grammar
- Keezhadi excavations (Tamil Nadu, 2015–present) — 60–80% structural overlap between IVC signs and early Tamil pot-shard graffiti marks

---

## Statistical Tests

### Proof 1 — P385 Suffix Theorem

Sign P385 (the jar pictogram) is proposed as the Proto-Dravidian masculine nominal suffix *-an* (e.g. *Meenan*, *Murugan*, *Velan*). A genuine suffix must be positionally constrained: terminal, never initial.

| Metric | Value |
|--------|-------|
| Terminal rate | 100% (pilot corpus) |
| Initial occurrences | 0 |
| p-value (binomial test) | 6.54 × 10⁻²¹ |
| Null hypothesis | rejected |

### Proof 2 — Positional Entropy

Agglutinative grammars constrain which morphemes may appear at each position, producing lower Shannon entropy at inscription boundaries. Positional entropy drops 0.488 bits from position 0 to position 1 — directionally consistent with agglutination, but requiring the full ICIT corpus (5,509 texts) to reach statistical significance.

### Proof 3 — Murugan Semantic Cluster

Signs P316 (vel/spear), P122 (meen/star), and P062 (malai/mountain) are the three primary iconographic attributes of Murugan, the oldest continuously attested deity in Tamil tradition. Chi-square co-occurrence test on the pilot corpus is directional but not yet significant — the cluster test requires greater corpus depth to be conclusive.

### Proof 4 — P122→P385 Agglutination Ratio

The bigram P122→P385 (*meen* + *-an* = *மீனன்*, 'Lord of Stars') occurs **6.92×** more often than independent sign probabilities predict. This is the agglutinative word-formation signature of Tamil.

---

## Adversarial Defenses

Four pre-emptive responses to standard academic critiques:

| Defense | Critique | Result |
|---------|----------|--------|
| D1 — Length filter | Short inscriptions inflate suffix statistics | p = 7.78×10⁻²⁰ on inscriptions of length ≥ 3 |
| D2 — Sanskrit genitive | P385 = Sanskrit genitive *-as*, not Tamil *-an* | P385 follows numerals/feminine stems zero times; Sanskrit *-as* must |
| D3 — Corpus integrity | Fragmentary seals inflate terminal counts | Pilot corpus is 100% intact (no fragments) |
| D4 — Repetition anomaly | A singular suffix should not double | P385 exhibits zero doubling; sign P062 doubles, consistent with Proto-Dravidian nominal reduplication |

---

## Sign Reference (Parpola 1994 + Mahadevan 1977)

Phonology mapped via Burrow & Emeneau, *Dravidian Etymological Dictionary* (DEDR, 1984).

| Sign | Tamil | Roman | Meaning | DEDR |
|------|-------|-------|---------|------|
| P122 | மீன் | meen | fish / star | DEDR-4889 |
| P385 | -அன் | -an | masculine nominal suffix | Proto-Dravidian grammar |
| P316 | வேல் | vel | spear (Murugan's weapon) | DEDR-5541 |
| P060 | கோ | ko | king / lord | DEDR-2178 |
| P062 | மலை | malai | mountain | DEDR-4710 |
| P091 | ஆறு | aaru | six / river | DEDR-338 |
| P311 | குடம் | kudam | jar / vessel | DEDR-1712 |

---

## Quick Start

```bash
pip install -r requirements.txt
python indus_decode.py        # runs all four proofs; writes results/
python adversarial_defense.py # runs all four defenses
```

Jupyter notebooks for each proof are in `notebooks/`.

---

## Corpus & Data

**Pilot corpus:** 41 representative seals transcribed from Parpola CISI Vol. I–II, spanning Mohenjo-Daro, Harappa, Dholavira, and Gulf/Dilmun sites.

**Full corpus:** 5,509 inscribed texts available via the ICIT database at [indus.epigraphica.de](https://indus.epigraphica.de) (registration required). The Mahadevan concordance (1977) is freely available on the [Internet Archive](https://archive.org). Researchers who have obtained the ICIT dataset are invited to replace the pilot corpus and rerun the analysis.

---

## Keezhadi Connection

Excavations at Keezhadi on the Vaigai river (Tamil Nadu) have yielded pot-shard graffiti marks with 60–80% structural correspondence to Indus signs, including variants of the terminal jar sign and geometric combinations. This provides stratigraphic evidence of symbol continuity from the Indus basin into the Tamil heartland, spanning approximately 2600 BCE to the 6th century BCE.

---

## Limitations

- **Corpus depth:** 41 seals is sufficient to demonstrate Proof 1 and Proof 4; Proofs 2 and 3 require the full 5,509-text ICIT corpus to reach significance.
- **No bilingual anchor:** without an equivalent of the Rosetta Stone, phonetic readings remain probabilistic. The suffix theorem is structural, not phonemic.
- **Institutional access:** the full Mahadevan corpus is published in physical form (1977); the ICIT database requires researcher registration. Wider open access would accelerate independent verification.

The Tamil Nadu government's **Iravatham Mahadevan Prize** (₹8.5 crore, ≈ USD 1M) for a verified decipherment remains unclaimed as of 2026.

---

## Prior Work

- [Kee2u/Deciphering_the_Indus_Valley_Script](https://github.com/Kee2u/Deciphering_the_Indus_Valley_Script) — PostgreSQL + SVM approach; obtained ICIT access from A. Fuls
- [ramnerd/IVC_script_decoded](https://github.com/ramnerd/IVC_script_decoded) — structural correlation with Old Tamil
- [Sukii/decipher-ivc](https://github.com/Sukii/decipher-ivc) — logo-syllabic Tamil mapping

---

## Contributing

Fork this repository, obtain the ICIT corpus from [indus.epigraphica.de](https://indus.epigraphica.de), replace the pilot corpus in `indus_decode.py`, and rerun. Pull requests with extended corpus results are welcome.

---

## License

MIT
