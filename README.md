**English** · [Português](README.pt.md)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20821058.svg)](https://doi.org/10.5281/zenodo.20821058)

# Hierarchical Bits (BH)

> **A structural envelope: it represents a heterogeneous asset, navigates parts
> of it without loading everything, and delegates each region to the best
> specialist format.**

📄 **Read online (bilingual site):** https://mmcarvalhodev.github.io/hierarchical-bits/

Most formats force you to pick **one**: *compact* (JPEG/WebP — but to see one
piece, you decode all of it) **or** *navigable* (indexes, OLAP, vector DB — but
it's structure bolted on top, across several systems that must be kept in sync).
BH writes **one envelope** where structure is part of the format: compact **and**
navigable, in a single file.

```
1. makes structure EXPLICIT   — hierarchy, belonging (cost: 0–6%)
2. ROUTES each region          — photo→WebP, gradient→formula, text→PNG
3. allows MULTIPLE readings    — preview / region / aggregate / proof
```

## The core capability (not a benchmark)

The heart of BH is not "being smaller". It's **reading only the part you need,
without decoding the rest** — a property of the format, not of a dataset.

**`bhmem`** ([`bhmem/`](bhmem/)) is the first usable artifact: agent memory as
`.bh`. The agent reads the summary, a topic, a time window or the provenance
**without loading the whole memory** (measured in real bytes read):

| reading | bytes read | vs flat store (reads all) |
|---|---|---|
| `summary()` — digest of all topics | 2.5% | **35× less** |
| `recall(topic)` — one branch | 4.0% | **22× less** |
| `since(t)` — time window | 9.8% | **9× less** |
| `provenance(id)` — source of 1 memory | 10.8% | **8× less** |

## Where it pays off and where it delegates (the honest boundary)

```
WINS       STRUCTURE-dominant data: documents, diagrams, layered data,
           structured AI outputs, symbolic knowledge. At the limit (rule-
           generated data): the payload becomes the PROGRAM that generates it
           — 800–3,600×.
DELEGATES  dense signal (photo, audio, embedding) → WebP/AVIF/HNSW reign, and
           BH CALLS them. It doesn't compete where it shouldn't.
```

The boundary is not entropy — it's **structure recognition**.

## What's in this repository

| | |
|---|---|
| [`BH_MASTER.en.md`](BH_MASTER.en.md) | The serious study: 9 angles tested, declared method, honest baselines, public self-corrections, Related Work. |
| [`BH_PITCH_APRESENTACAO.en.md`](BH_PITCH_APRESENTACAO.en.md) | Presentation pitch (7 slides). |
| [`BH_PITCH_VISUAL.en.md`](BH_PITCH_VISUAL.en.md) + [`pitch_assets/en/`](pitch_assets/en/) | Pitch with 4 comparative charts. |
| [`bhmem/`](bhmem/) | **Usable prototype** — agent memory as `.bh` (lib + tests, 35×/22×/9×/8×). |
| [`bhtrace/`](bhtrace/) | **Usable prototype** — a distributed trace as `.bh` (read the skeleton without the payload, ~9× less). |
| [`bhckpt/`](bhckpt/) | **Usable prototype** — a model checkpoint as `.bh` (architecture without weights ~1,800× less; load one MoE expert ~20× less). |
| [`bhanno/`](bhanno/) | **Usable prototype** — adversarial annotations (K rival labelings over one substrate, ~4.6× vs K copies; adjudication reads labels only). |
| `db/` `merkle/` `wafer/` `gpu/` `compositional/` … | The terrains tested, each with code + `RESULTS_*.md`. |

*Portuguese originals: `BH_MASTER.md`, `BH_PITCH_APRESENTACAO.md`,
`BH_PITCH_VISUAL.md`. The site (`build_site.py`) builds both languages.*

## Reproduce

```bash
python bhmem/demo.py                      # measured demo + tests
python -m pytest bhmem/tests/ -q
python pitch_assets/generate_charts.py    # charts PT + EN
python pitch_assets/generate_evidence.py
python build_site.py                      # bilingual site (EN default + PT)
```

## Licenses (dual)

- **Code** (`*.py`, tests, benchmarks) → **Apache License 2.0** — see
  [`LICENSE`](LICENSE). Permissive, with an explicit patent grant.
- **Documents** (`*.md` study, report, pitch) → **CC BY 4.0** — see
  [`LICENSE-docs.md`](LICENSE-docs.md). Cite, translate, redistribute,
  including commercially, keeping the attribution.

## Author & citation

**Márcio M. Carvalho** (2025–2026).

> Carvalho, Márcio M. *Hierarchical Bits — A study of a structural envelope.*
> 2025–2026. Documentation license: CC BY 4.0.

---

*"The value isn't in the compressed block. It's in the structure that knows what
that block means."*
