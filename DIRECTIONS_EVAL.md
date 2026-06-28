# Directions evaluated — explored frontiers (validated dead-ends)

> A map is more useful when it marks where the roads *don't* go. Three
> application directions for BH were proposed (by AI sessions) as "future work."
> Rather than ship them as features or quietly drop them, we **tested them** —
> real bytes, real seeks, honest baselines — and record the outcome here. The
> tests are runnable in [`directions/`](directions/); each has a `RESULTS_*.md`.

## Summary

Section "11 — Application Directions", generated in AI sessions, was submitted to
falsifiable tests (real bytes, seeks, honest baselines). **Result: the mechanisms
re-derived known SOTA (ANCHOR) and, in the Edge/IoT case, lost to a trivial
baseline because of the Read-Face round-trip cost.** They were **not** integrated
into the BH core and are **not** presented in the Zenodo record as features. They
are kept in [`directions/`](directions/) as a record of methodology and of the
boundary of scope.

## What was tested, and what it measured

| direction | claim tested | measured outcome | verdict |
|---|---|---|---|
| **Edge / IoT progressive transmission** | "BH-stream sends far fewer bytes at high recall" | 13× fewer than full transmission (recall 1.0) — but **1.88× MORE bytes than a trivial fixed-threshold filter** (which itself does 25×). The summary stream + request round-trip costs bytes every window. | **refuted vs SOTA** — wins only vs naive full transmission |
| **BIM / Digital Twins targeted read** | "a thermal analysis reads only thermal+geometry → big savings" | the flagship query saves only **1.1×** (geometry dominates and is needed); real savings appear only for queries that *skip* geometry (cost-only 11.6×) | **ANCHOR** — partial loading (IFC/glTF already do it); and it tests selective-read, not the FCIR angle the sweep flagged for BIM |
| **Structural RAG** | "a structural read reduces hallucination at matched retrieval cost" | byte/locate economics confirmed (skeleton = **2.2%** of the doc; scoped read **4.6%**) — but the **hallucination claim needs an LLM eval and was not tested** | **economics = ANCHOR; the actual claim remains open/untested** |

## Why this is here (and not hidden)

In serious computer science, publishing **validated dead-ends** raises the
author's credibility. A reviewer who sees *"he tested IoT, BIM and structural
RAG, measured the bytes, found Edge/IoT lost to a trivial baseline because of the
round-trip overhead, and discarded it"* concludes: this author is drawing a real
map of what the technology can and cannot do — not selling something.

Two further honest points the tests surfaced:

- **All three are the substrate-sharing / selective-read mechanism**, which the
  20-domain sweep ([`applicability/`](applicability/)) already found to be mature
  SOTA. None of them engages **FCIR** (the rival-interpretation property the
  investigation identified as the actual differentiator — see
  [`BH_PRINCIPLE.md`](BH_PRINCIPLE.md)).
- The one direction with a real future is **BIM via the *right* angle** — rival
  discipline overlays (arch/structural/MEP disagreeing over one element), which is
  the FCIR/BUILD case, not the selective-read case tested here. That would be a
  prototype, not a feature claim.

## Reproduce

```
X:/miniconda3/python.exe directions/edge_test.py   # -> directions/RESULTS_11_2_EDGE.md
X:/miniconda3/python.exe directions/bim_test.py    # -> directions/RESULTS_11_3_BIM.md
X:/miniconda3/python.exe directions/rag_test.py    # -> directions/RESULTS_11_1_RAG.md
```
