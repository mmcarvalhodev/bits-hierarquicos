"""Re-score the domains on the FCIR property 3-4 (preserved disagreement), not 1-2.

The original scorecard (scorecard.py) weighted substrate-sharing + selective read
(properties 1-2), which are already SOTA — so most domains came back ANCHOR. The
meta-critique is right that this is the wrong lens for the differentiator. Here we
re-score on the question that actually tests properties 3-4:

  "Do rival / contradictory interpretations exist, are they destroyed by current
   adjudication, is the disagreement itself signal — and is there NO existing tool
   that keeps them queryable?"

HONEST BASELINE (the crux): the baseline for 'queryable disagreement' is NOT a
gold-collapsed store. It is an UNCOLLAPSED (item, source, value) table, which
CrowdTruth / human-label-variation datasets / named graphs / any annotation DB
already provide, and over which the disagreement queries are plain GROUP BY (see
directions/RESULTS_DISAGREEMENT_COMPUTE.md). So `capability_gap` is HIGH only
where even that uncollapsed-table practice is not standard.

  composite = (0.30*disagreement_real + 0.25*collapsed_today
             + 0.25*disagreement_is_signal + 0.20*capability_gap) / 3 * 100

Verdicts:
  N/A     — no rival interpretations (the 1-2 domains; correctly drop here)
  STANCE  — disagreement matters and is collapsed today, BUT an uncollapsed table
            already gives the capability; FCIR's value is the discipline + co-registration
  BUILD   — disagreement matters AND no standard tool keeps it queryable (capability gap)

Scores are reasoned estimates (transparent), not market data.
Run: X:/miniconda3/python.exe applicability/rescore_fcir.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
W = {"dis": 0.30, "col": 0.25, "sig": 0.25, "gap": 0.20}

# domain, disagreement_real, collapsed_today, disagreement_is_signal, capability_gap, note
ROWS = [
    ("Multi-agent AI memory", 3, 3, 3, 2, "agents forced to consensus; no standard queryable disagreement layer"),
    ("Clinical-trial adjudication", 3, 2, 3, 2, "committees converge to one endpoint; disagreement pattern manual/post-hoc"),
    ("Intelligence analysis", 3, 2, 3, 2, "source-reliability disagreement is the signal; systems converge to one assessment"),
    ("Model alignment / red-teaming", 3, 2, 3, 2, "red/blue disagreement is diagnostic; logged but not a queryable layer"),
    ("Regulatory divergence (EU/US)", 3, 2, 2, 2, "firms keep SEPARATE systems per jurisdiction (duplication, not co-registration)"),
    ("Data labeling / annotation", 3, 2, 3, 1, "disagreement real & signal, BUT CrowdTruth / uncollapsed tables already keep it"),
    ("RLHF / preference data", 3, 2, 3, 1, "increasingly kept per-annotator; uncollapsed tables do the queries"),
    ("Medical imaging (multi-reader)", 3, 2, 3, 1, "DICOM SEG keeps multiple; adjudication often collapses downstream"),
    ("Knowledge graphs (multi-ontology)", 3, 1, 2, 1, "named graphs + SPARQL already keep & query rival triples"),
    ("Legal eDiscovery (multi-reviewer)", 2, 2, 2, 1, "reviewer disagreement tracked as QC; tables already do it"),
    ("Video / MAM (human vs AI tags)", 2, 2, 2, 1, "conflicting tags logged with provenance; queryable already"),
    ("Genomics (multi-caller)", 2, 1, 2, 1, "bcftools isec already compares rival VCFs"),
    ("Dataset versioning / data lakes", 1, 1, 1, 0, "versions, not contradictory interpretations of the same element"),
    ("Earth obs / satellite", 1, 1, 1, 0, "co-registered products, rarely contradictory rival readings"),
    ("Model checkpoints / MoE", 1, 0, 0, 0, "adapters are alternatives, not contradictions; no adjudication"),
    ("Distributed tracing", 0, 0, 0, 0, "no rival interpretations of a span"),
    ("Time-series / IoT", 0, 0, 0, 0, "single signal value; no contradiction"),
    ("Image / audio codecs", 0, 0, 0, 0, "one perceptual ground truth"),
    ("Vector DBs / embeddings", 0, 0, 1, 0, "model variants exist but not contradictory readings of one element"),
]

VCOLOR = {"BUILD": "#2e7d32", "STANCE": "#1565c0", "N/A": "#90a4ae"}


def composite(dis, col, sig, gap):
    return (W["dis"]*dis + W["col"]*col + W["sig"]*sig + W["gap"]*gap) / 3 * 100


def verdict(dis, col, sig, gap):
    if dis <= 1:
        return "N/A"
    if gap >= 2 and col >= 2:
        return "BUILD"
    return "STANCE"


def main():
    scored = []
    for (name, dis, col, sig, gap, note) in ROWS:
        scored.append({"name": name, "c": round(composite(dis, col, sig, gap), 1),
                       "v": verdict(dis, col, sig, gap), "note": note,
                       "dis": dis, "col": col, "sig": sig, "gap": gap})
    scored.sort(key=lambda r: r["c"], reverse=True)

    fig, ax = plt.subplots(figsize=(11, 7.5))
    ys = range(len(scored))
    ax.barh(list(ys), [r["c"] for r in scored],
            color=[VCOLOR[r["v"]] for r in scored], height=.72)
    for y, r in zip(ys, scored):
        ax.text(r["c"] + 1, y, f"{r['c']:.0f} · {r['v']}", va="center", fontsize=8.5,
                fontweight="bold", color=VCOLOR[r["v"]])
    ax.set_yticks(list(ys)); ax.set_yticklabels([r["name"] for r in scored], fontsize=9)
    ax.invert_yaxis(); ax.set_xlim(0, 110)
    ax.set_xlabel("FCIR property-3-4 score (preserved disagreement)  ·  weights: "
                  "disagreement .30, collapsed-today .25, is-signal .25, capability-gap .20", fontsize=8.5)
    ax.set_title("Re-score on the RIGHT property (3-4: preserved disagreement)\n"
                 "vs the honest baseline (uncollapsed table) — not gold-collapse",
                 fontweight="bold", fontsize=12, pad=12)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in VCOLOR.values()]
    ax.legend(handles, ["BUILD — capability gap (no standard tool keeps it queryable)",
                        "STANCE — worth preserving, but an uncollapsed table already does it",
                        "N/A — no rival interpretations"], loc="lower right", fontsize=8, framealpha=.95)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "rescore_fcir_map.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    L = ["# Re-score on FCIR property 3-4 (preserved disagreement) — the right lens\n"]
    L.append("> The original [scorecard](APPLICABILITY_SCORECARD.md) weighted properties 1-2 "
             "(substrate + selective read), already SOTA → mostly ANCHOR. The meta-critique was "
             "right that this is the wrong lens. Here we re-score on **property 3-4** with the "
             "**honest baseline** (an uncollapsed `(item, source, value)` table, not a "
             "gold-collapsed store — see `../directions/RESULTS_DISAGREEMENT_COMPUTE.md`).\n")
    L.append("![map](rescore_fcir_map.png)\n")
    L.append("| # | domain | score | verdict | why |")
    L.append("|---|---|---|---|---|")
    for i, r in enumerate(scored, 1):
        L.append(f"| {i} | {r['name']} | **{r['c']:.0f}** | {r['v']} | {r['note']} |")
    L.append("\n## What the re-score shows (honest)\n")
    L.append("1. **The map does invert — the critique was right about that.** The 1-2 ANCHOR "
             "domains (codecs, traces, checkpoints, lakeFS, satellite) **drop to N/A** here: they "
             "have no rival interpretations. The disagreement-rich domains rise.")
    L.append("2. **But almost all the risers are `STANCE`, not `BUILD`.** Disagreement matters and "
             "is often collapsed today — yet the *capability* to keep it queryable already exists "
             "in an uncollapsed table (CrowdTruth, named graphs, per-annotator datasets). FCIR's "
             "value there is the **discipline** (don't collapse on write) + **co-registration**, "
             "not a new capability. This matches the disagreement-compute test: gold-collapse 0/4, "
             "uncollapsed table 4/4.")
    L.append("3. **The genuine `BUILD` candidates are where no standard tool keeps it queryable:** "
             "**multi-agent AI memory** (the clearest — agents forced to consensus, no queryable "
             "disagreement layer), and arguably **clinical-trial adjudication, intel analysis, "
             "red-teaming, regulatory divergence** (workflows manual/siloed). These are "
             "*untested hypotheses* — the same status as any direction until measured.")
    L.append("\n**Net:** re-scoring on the right property corrects the bias the critique exposed, "
             "**and** confirms the honest conclusion: the value is preserving disagreement as a "
             "discipline/model (FCIR), not a capability that does not exist elsewhere. The one "
             "place worth building is **multi-agent memory** — exercised next in `bhmemx/`.")
    (OUT / "RESCORE_FCIR.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print("RE-SCORE on property 3-4:")
    for i, r in enumerate(scored, 1):
        print(f"  {i:2d}. {r['c']:5.1f}  {r['v']:7s}  {r['name']}")
    print("\nwrote RESCORE_FCIR.md + rescore_fcir_map.png")


if __name__ == "__main__":
    main()
