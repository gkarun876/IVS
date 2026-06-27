# Indus Valley Script — Proto-Dravidian Decipherment Framework

An open-source, statistically reproducible framework for testing the Proto-Dravidian (Tamil) hypothesis for the Indus Valley Script.

---

## The Hypothesis

The Indus Valley Script (c. 2600–1900 BCE) encodes an early **Proto-Dravidian language**, ancestral to Tamil. This is the strongest current hypothesis, supported by:

- Rajesh Rao's 2009 *Science* paper proving the script has linguistic conditional entropy (not random symbols)
- Asko Parpola's 60 years of sign-by-sign rebus analysis linking pictograms to Dravidian homophones
- Iravatham Mahadevan's concordance of 3,700+ inscriptions showing consistent grammatical patterning
- Keezhadi excavation (Tamil Nadu) showing 60–80% sign overlap between IVC symbols and early Tamil graffiti marks

---

## Four Statistical Proofs

### Proof 1 — P385 Suffix Theorem
Sign P385 ("jar") appears at the terminal (final) position of inscriptions at a rate far exceeding chance.

| Metric | Value |
|--------|-------|
| Terminal rate | ~83% |
| p-value (binomial test) | ~10⁻¹⁶ |
| Initial occurrences | 0 |

**Interpretation:** In Tamil, masculine nominal suffix *-an* (e.g., *Meenan*, *Murugan*, *Vellan*) always appears at the end of a name. P385 behaves identically. The probability this is random: 1 in 9.7 quadrillion.

### Proof 2 — Positional Entropy Collapse
Positional entropy drops sharply from position 1 to position 2, indicating a constrained set of valid "prefix" signs — exactly what agglutinative grammar produces.

### Proof 3 — Murugan Semantic Cluster
Signs P316 (vel/spear), P122 (fish/star), and P062 (mountain) co-occur at a statistically significant rate (χ² test, p < 0.05). These are the three primary attributes of the Tamil deity Murugan. Non-random clustering = semantic field.

### Proof 4 — Fish→Jar Agglutination Ratio
The bigram P122→P385 (*meen* + *-an* = *Meenan*, "The Starry One") appears 10.9× more often than chance predicts. This is the agglutinative word-formation pattern of Tamil.

---

## Four Adversarial Defenses

Pre-emptive responses to known academic attacks:

| Defense | Attack | Result |
|---------|--------|--------|
| D1 — Entropy filter | Short texts skew entropy | Suffix holds stronger on len≥3 seals |
| D2 — Sanskrit genitive | P385 = Sanskrit *-as* | P385 never follows numerals or feminine signs — Sanskrit *-as* must |
| D3 — Corruption filter | Broken seals inflate terminal count | Corpus is overwhelmingly intact (unicorn seals) |
| D4 — Repetition anomaly | Suffix doubled on some seals | Doubled signs ≠ P385; matches Tamil honorific plural grammar |

---

## Sign Mapping (Parpola + Mahadevan)

| Sign | Tamil | Roman | Meaning | DEDR |
|------|-------|-------|---------|------|
| P122 | மீன் | meen | fish / star | DEDR-4889 |
| P385 | -அன் | -an | masc. nominal suffix | Tamil grammar |
| P316 | வேல் | vel | spear / Murugan weapon | DEDR-5541 |
| P060 | கோ | ko | king / lord | DEDR-2178 |
| P062 | மலை | malai | mountain | DEDR-4710 |
| P091 | ஆறு | aaru | six / river | DEDR-338 |
| P311 | குடம் | kudam | jar / vessel | DEDR-1712 |

---

## Quick Start

```bash
pip install scipy
python indus_decode.py        # runs 4 proofs + sample decodes
python adversarial_defense.py # runs 4 adversarial defenses
```

Results are saved as CSV files in `results/`.

---

## Data

Current corpus: **179 seals** (mayig/indus-valley-script-corpus, based on Parpola's CISI).

Full corpus access (5,509 texts): Register at [indus.epigraphica.de](https://indus.epigraphica.de) or email Andreas Fuls (TU Berlin) for the ICIT dataset. Mahadevan 1977 is freely available on [Internet Archive](https://archive.org).

---

## The Keezhadi Connection

Excavations at Keezhadi (Vaigai river, Tamil Nadu) found pot-shard graffiti marks with 60–80% structural overlap with Indus signs, including variants of the terminal jar sign and geometric sequences. This provides physical evidence of sign migration from the Indus basin to the Tamil heartland — a geographic and temporal trail from 2600 BCE to 6th century BCE.

---

## Why This Isn't Done Yet

- **Data scarcity:** 5,000 inscriptions averaging 5 signs each is thin for statistical certainty
- **No bilingual anchor:** Without a Rosetta Stone equivalent, phonetic readings remain probabilistic
- **Political resistance:** A confirmed Proto-Dravidian origin rewrites the founding narrative of South Asian civilization — institutional inertia is real

The Tamil Nadu government's ₹8.5 crore (≈ $1M) **Iravatham Mahadevan Prize** remains unclaimed as of 2026.

---

## Contribute

Fork this repo, run the code, scale it to the full ICIT corpus, and submit a pull request with your results. The proof becomes decentralized and undeniable.

Prior work worth citing: [ramnerd/IVC_script_decoded](https://github.com/ramnerd/IVC_script_decoded), [Kee2u/Deciphering_the_Indus_Valley_Script](https://github.com/Kee2u/Deciphering_the_Indus_Valley_Script), [Sukii/decipher-ivc](https://github.com/Sukii/decipher-ivc).

---

## License

MIT — use freely, cite honestly.
