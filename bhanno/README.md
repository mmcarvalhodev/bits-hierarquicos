# bhanno — adversarial annotations over a shared substrate

> The Hierarchical Bits thesis at full strength: the **matrix of adverse
> interpretations**. The fourth `.bh` prototype — *one envelope, four domains*
> ([`bhmem`](../bhmem/), [`bhtrace`](../bhtrace/), [`bhckpt`](../bhckpt/), bhanno).

The same data (the **substrate** — images, documents, signals) is recorded
**once**, and K annotators lay down co-registered interpretation layers that may
**disagree**. This is the wafer terrain (§3.4 of the study) generalized from
*additive* layers (RGB+depth+segmentation) to **rival** layers (K labelings that
contest each other).

The capability no current format offers: **hold K competing interpretations
without duplicating the substrate.** Today, K interpretations = K annotated
copies (the heavy substrate stored K times). bhanno stores it once and
co-registers K thin label layers:

```python
from bhanno import AnnotationStore, AnnotationReader

store = AnnotationStore("imgset", ["alice", "bob", "carol"])
store.add_item("img0001", raw_bytes)               # the shared substrate, once
store.add_label("alice", "img0001", {"class": 3})  # a layer
store.add_label("bob",   "img0001", {"class": 7})  # a rival layer (disagrees)
store.save("annotations.bha")

an = AnnotationReader("annotations.bha")
an.item("img0001")        # the shared substrate of one item       — its block
an.layer("alice")         # one annotator's whole interpretation    — its layer
an.item_views("img0001")  # ALL K views of one item (the matrix)    — K small blocks
an.disagreements()        # where annotators contest — labels only, no substrate
an.adjudicate()           # majority + agreement rate — labels only
```

## 1. Hold K rival interpretations for ~the price of one

Realistic demo (200 items, 6 KB substrate each, 5 annotators who disagree):

| | |
|---|---|
| `.bha` (substrate **once** + 5 label layers) | **1.32 MB** |
| 5 independent annotated copies (substrate ×5) | **6.07 MB** |
| **saving** | **4.6× smaller** |

The saving approaches **K** as the substrate dominates the per-layer residual —
the wafer law. Five contesting interpretations, one substrate.

## 2. Adjudication is a structural read (labels only)

| reading | % of file read | vs full |
|---|---|---|
| `disagreements()` / `adjudicate()` — find the contest, **no substrate** | 8.8% | **11× less** |
| `item_views(id)` — all K views of one item | 4.3% | **23× less** |
| `item(id)` / `layer(a)` | ~5% | ~20× less |

In the demo: **62% agreement** (125 unanimous, **75 contested** of 200) — found
by reading only the label layers, never the 1.2 MB of substrate.

## The `.bha` format

```
MAGIC(4)
header_len(4) + header_json   {dataset_id, n_items, annotators:[...]}
itab_len(4)   + itab_json      substrate locators [{id, off, size}]
ltab_len(4)   + ltab_json      label locators {annotator: [{id, off, size}]}
substrate region               per-item bytes (shared, stored ONCE)
label region                   per-(annotator, item) label
```

The substrate is written once; each annotator adds only a layer over it.

## Honest boundary (the same as the study)

bhanno wins on the **shared-substrate / co-registered-rival-layers** structure.
It **surfaces** the contest — `adjudicate()` reports the majority and the
disagreement; **it does not decide who is right.** Resolving the truth is a
modeling choice the envelope exposes, not one it makes. Dense per-layer payloads
(e.g. full segmentation masks) are still delegated to whatever stores them best;
bhanno co-registers them over the one substrate.

## Run

```
X:/miniconda3/python.exe X:/bitH/bhanno/demo.py        # measured demo → RESULTS_BHANNO_DEMO.md
X:/miniconda3/python.exe -m pytest X:/bitH/bhanno/tests/ -q   # correctness as a gate (9/9)
```

## Status

A minimal, usable prototype — not a product. It does the full loop (build a
substrate + rival layers → save → read by structure → measure) with tested
correctness. It is the case where *"matrix of adverse interpretations"* stops
being an idea and becomes a number.
