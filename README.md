**English** · [Português](README.pt.md)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20821058.svg)](https://doi.org/10.5281/zenodo.20821058)

# Hierarchical Bits (BH)

> **Hierarchical Bits (BH) is a representation model where multiple — possibly
> contradictory — interpretations share one immutable substrate and stay
> queryable, without duplicating the data and without forcing them into a single
> truth.**

📄 **Read online (bilingual site):** https://mmcarvalhodev.github.io/hierarchical-bits/

The heart, in one line: **don't duplicate the world every time someone disagrees
with it.** Start from a common base — one dataset, one building, one document set,
one history. Over it, several interpretations naturally arise: annotators label
it, disciplines read it differently, hypotheses compete over it, versions
accumulate. Today, holding them forces a bad choice — **copy the base** once per
interpretation, or **merge to one** and lose the rest.

![FCIR — the model in one picture: rival interpretations co-registered over one immutable substrate, with optional read-time adjudication](pitch_assets/fcir_diagram.svg)

## What makes it different — and what doesn't

Storing a substrate once and reading it selectively is **already mature SOTA** —
DICOM, COG/STAC, lakeFS, CRAM/tabix, S-LoRA, MAM. BH does **not** claim to invent
that. A [20-domain sweep](applicability/) pointed to the still-under-explored
property, which we give a **working name**: the **First-Class Interpretation
Representation (FCIR)** — interpretations kept as persistent, addressable,
co-equal entities over a shared substrate, with adjudication **deferred and
optional**.

> The honest claim, scoped to what we surveyed: **our investigation identified
> FCIR as the property that best distinguishes BH from the approaches evaluated**
> — a result, not a universal law, and a working name that should follow the idea
> rather than cage it. See [`BH_PRINCIPLE.md`](BH_PRINCIPLE.md).

**The distinguishing test (falsifiable):** given two interpretations that
disagree about the same element, can **both remain** — neither marked wrong —
until a reader chooses (or declines) to adjudicate? Many systems converge to one
truth, or isolate each reading into an independent copy/version. BH keeps them
co-registered over one substrate and lets adjudication wait.

## Prior art — honestly

A blind read test had five independent reviewers immediately name systems that
already do parts of this. They were right, and **two already do it in full**,
each in its domain: **RDF named graphs + provenance** (for triples) and
**standoff annotation** (W3C Web Annotation, UIMA — for text/media; our `bhanno`
prototype *is* standoff annotation, it did not invent it). Git branches,
bitemporal DBs / Datomic, CRDTs, and event sourcing each do an *adjacent but
distinct* thing (eventual merge, temporal supersession, auto-convergence, derived
views).

So **FCIR is not a new mechanism** — it is an **architectural synthesis and a
name**: one term + one falsifiable test for a property that today exists only
domain-by-domain, with no shared vocabulary across triples, annotation, BIM,
model weights, and agent memory. **Judge it as a synthesis, not an invention.**
Full confrontation — including where existing systems already win — is in
[`BH_PRINCIPLE.md`](BH_PRINCIPLE.md#how-fcir-relates-to-adjacent-systems).

## What's in this repository

| | |
|---|---|
| [`BH_PRINCIPLE.md`](BH_PRINCIPLE.md) | **The concept** — FCIR (working name), the falsifiable test, and the honest confrontation with adjacent systems. |
| [`BH_ALGEBRA.md`](BH_ALGEBRA.md) | **The formal model** — operators + laws; FCIR as `⊕ ⊥ α` (coexistence decoupled from adjudication). |
| [`CONCLUSION.md`](CONCLUSION.md) | **Provisional conclusion** — the universal-paradigm hypothesis was not confirmed; what survived; response to external critique. |
| [`applicability/`](applicability/) | The 20-domain sweep, scored and ranked (mostly ANCHOR; one BUILD). |
| [`BH_MASTER.en.md`](BH_MASTER.en.md) | The measured study: 9 angles tested, declared method, honest baselines, public self-corrections, Related Work. |
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

*"Don't duplicate the world every time someone disagrees with it."*
