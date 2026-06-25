"""bhanno demo — adversarial annotations over a shared substrate, measured.

Builds a dataset (heavy substrate) annotated by 5 annotators who DISAGREE,
writes it as one .bha, and measures the two things that matter:

  1. STORAGE — holding K rival interpretations as a shared substrate + K label
     layers, vs K independent annotated copies (the substrate duplicated K times).
  2. ADJUDICATION — finding where the annotators contest, reading the label
     layers only (never the substrate).

Run:  X:/miniconda3/python.exe X:/bitH/bhanno/demo.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhanno import AnnotationReader, AnnotationStore  # noqa: E402

OUT = Path(__file__).resolve().parent
N_ITEMS, N_CLASSES, SUBSTRATE_BYTES = 200, 10, 6000
ANNOTATORS = ["alice", "bob", "carol", "dave", "erin"]


def build() -> AnnotationStore:
    """A small image dataset: heavy substrate (the pixels), light labels (a
    class + bbox), and 5 annotators who agree on most items and contest the
    ambiguous ones. The substrate is recorded ONCE; each annotator is a layer."""
    rng = random.Random(0)
    npr = np.random.default_rng(0)
    store = AnnotationStore("imgset-v1", ANNOTATORS)

    for i in range(N_ITEMS):
        item_id = f"img{i:04d}"
        store.add_item(item_id, npr.integers(0, 256, SUBSTRATE_BYTES, dtype=np.uint8).tobytes())
        # ground-ish truth; ~15% of items are genuinely ambiguous (two plausible classes)
        ambiguous = rng.random() < 0.15
        true_c = rng.randrange(N_CLASSES)
        alt_c = (true_c + 1 + rng.randrange(N_CLASSES - 1)) % N_CLASSES
        for a in ANNOTATORS:
            if ambiguous:
                c = rng.choice([true_c, alt_c])          # annotators split
            else:
                c = true_c if rng.random() < 0.92 else rng.randrange(N_CLASSES)  # per-annotator noise
            store.add_label(a, item_id, {
                "class": c,
                "confidence": round(rng.uniform(0.55, 0.99), 2),
                "bbox": [rng.randint(0, 200), rng.randint(0, 200),
                         rng.randint(20, 120), rng.randint(20, 120)],
            })
    return store


def main() -> None:
    store = build()
    bha = OUT / "annotations.bha"
    store.save(bha)
    reader = AnnotationReader(bha)
    fsize = reader.file_size

    L: list[str] = []
    p = L.append
    p("# bhanno — adversarial annotations over a shared substrate (measured demo)\n")
    sc = reader.storage_comparison()
    p(f"- items: **{sc['substrate_bytes']//SUBSTRATE_BYTES}** · annotators: "
      f"**{sc['annotators']}** · substrate: **{sc['substrate_bytes']/1e6:.2f} MB** · "
      f"labels: **{sc['label_bytes']/1e3:.0f} KB**\n")

    p("## 1. The matrix of interpretations: shared substrate vs K copies\n")
    p("Holding K rival interpretations the usual way means **K annotated copies** "
      "— the heavy substrate stored K times. bhanno stores it **once** and "
      "co-registers K label layers.\n")
    p(f"| | bytes |\n|---|---|")
    p(f"| `.bha` (substrate once + {sc['annotators']} layers) | **{sc['bha_bytes']:,} B** |")
    p(f"| {sc['annotators']} independent annotated copies | {sc['independent_copies_bytes']:,} B |")
    p(f"| **saving** | **{sc['saving']}× smaller** |\n")
    p(f"> Hold {sc['annotators']} contesting interpretations for ~the price of one "
      f"substrate + {sc['annotators']} thin layers. The saving approaches K as the "
      "substrate dominates — the wafer law (§3.4).\n")

    p("## 2. The readings (real bytes read)\n")
    p("| reading | what it returns | bytes read | % of file | vs full |")
    p("|---|---|---|---|---|")

    def row(label, what, stats, n):
        ratio = fsize / stats.bytes_read if stats.bytes_read else float("inf")
        p(f"| `{label}` | {what} ({n}) | {stats.bytes_read:,} B | "
          f"{stats.fraction*100:.1f}% | **{ratio:.0f}× less** |")

    # a contested item, for item_views
    contested, _ = reader.disagreements()
    cid = contested[0]["id"] if contested else reader.itab[0]["id"]

    it, st = reader.item(reader.itab[0]["id"]); row("item(id)", "one shared substrate", st, 1)
    lv, st = reader.layer("alice"); row("layer('alice')", "one annotator's labels", st, len(lv))
    iv, st = reader.item_views(cid); row(f"item_views('{cid}')", "ALL K views of one item", st, len(iv))
    dg, st = reader.disagreements(); row("disagreements()", "contested items (labels only)", st, len(dg))
    aj, st = reader.adjudicate(); row("adjudicate()", "majority + agreement (labels only)", st, aj["n_items"])
    fl, st = reader.full(); row("full()", "everything (baseline)", st, len(fl["items"]))

    p("\n## 3. Adjudication (read from labels only, no substrate touched)\n")
    p(f"- agreement rate: **{aj['agreement_rate']*100:.0f}%** "
      f"({aj['unanimous']} unanimous, **{aj['contested']} contested** of {aj['n_items']})")
    if contested:
        ex = contested[0]
        p(f"- example contested item `{ex['id']}`: votes {ex['votes']} → "
          f"majority **{ex['majority']}** (agreement {ex['agreement']*100:.0f}%)")
    p("\n## What this demonstrates\n")
    p("- **Adverse interpretations cost ~1 substrate, not K.** The capability no "
      "format offers: K contesting labelings co-registered over data stored once.")
    p("- **Adjudication is a structural read.** `disagreements()` / `adjudicate()` "
      "find the contested items reading **only the label layers** — never the "
      "heavy substrate.")
    p("- **Honest boundary.** bhanno surfaces the contest; it does not decide who "
      "is right. Resolving truth is a modeling choice the envelope exposes.")

    out = OUT / "RESULTS_BHANNO_DEMO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"items={N_ITEMS} annotators={len(ANNOTATORS)} bha={fsize}B "
          f"saving={sc['saving']}x agreement={aj['agreement_rate']*100:.0f}% "
          f"contested={aj['contested']}")
    for label, fn in [("item", lambda: reader.item(reader.itab[0]['id'])),
                      ("layer(alice)", lambda: reader.layer("alice")),
                      (f"item_views({cid})", lambda: reader.item_views(cid)),
                      ("disagreements", reader.disagreements),
                      ("adjudicate", reader.adjudicate), ("full", reader.full)]:
        _, s = fn()
        r = fsize / s.bytes_read if s.bytes_read else 0
        print(f"  {label:22s} {s.bytes_read:8d} B  {s.fraction*100:5.1f}%  {r:5.0f}x less")
    print(f"report: {out}")


if __name__ == "__main__":
    main()
