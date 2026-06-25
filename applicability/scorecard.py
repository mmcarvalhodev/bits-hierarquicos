"""BH applicability scorecard — synthesizes the research sweep into a ranked map.

Data: the 20-domain research sweep (one web-grounded agent per domain; see
SURVEY_SOURCES.md for the citations). Scores are 0-3 per criterion. The composite
is computed here with DECLARED weights so it is transparent and reproducible.

  composite = (0.30*substrate_dominance + 0.20*multiplicity + 0.20*selective_read
             + 0.15*structural_access + 0.15*adversarial) / 3 * 100   (0-100)

Verdict (from the research, captures novelty vs already-SOTA):
  BUILD    = strong fit AND the union is not yet a mainstream tool
  ANCHOR   = strong BH shape BUT store-once + selective-read already mature SOTA
  DELEGATE = dense signal — BH should call a specialist codec, not compete
  NO       = no real fit (substrate does not dominate / payload is the point)

Run:  X:/miniconda3/python.exe X:/bitH/applicability/scorecard.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
W = {"sd": 0.30, "mult": 0.20, "sr": 0.20, "sa": 0.15, "adv": 0.15}

# area, substrate_dominance, multiplicity, adversarial, selective_read,
# structural_access, verdict, built, scale, note
ROWS = [
    ("Knowledge graphs (multi-ontology)", 3, 3, 3, 3, 3, "ANCHOR", False, "16B triples", "named graphs + RDF-star already SOTA"),
    ("Medical imaging (multi-reader)", 3, 3, 3, 3, 2, "ANCHOR", False, "WSI 1-100 GB", "DICOM SEG references source — mature"),
    ("Earth obs / satellite", 3, 3, 3, 3, 2, "ANCHOR", False, "10+ PB", "COG + STAC already do it"),
    ("Legal eDiscovery", 3, 3, 3, 3, 2, "ANCHOR", False, "TB / matter", "Relativity store-once + coding fields"),
    ("Video archives / MAM", 3, 3, 3, 3, 2, "ANCHOR", False, "PB masters", "MAM timecoded tracks — mature"),
    ("Dataset versioning / data lakes", 3, 3, 3, 3, 2, "ANCHOR", False, "PB", "lakeFS/DVC zero-copy IS the win"),
    ("Data labeling / annotation", 3, 3, 3, 2, 3, "ANCHOR", True, "COCO 20 GB", "CVAT/Label Studio store-once — mature"),
    ("Genomics (variant calling)", 3, 2, 3, 3, 3, "ANCHOR", False, "ref 3 Gbp", "CRAM + tabix selective — mature"),
    ("Geospatial map tiles", 3, 3, 2, 3, 2, "ANCHOR", False, "PB", "COG/PMTiles/vector tiles — mature"),
    ("CAD / BIM", 2, 3, 3, 3, 3, "BUILD", False, "tens of GB", "federation duplicates; rival overlays UNSERVED"),
    ("Model checkpoints / MoE", 3, 3, 1, 3, 2, "ANCHOR", True, "base GB-TB", "S-LoRA / Punica already SOTA"),
    ("Agent memory", 1, 3, 3, 3, 2, "ANCHOR", True, "KB-MB text", "substrate LIGHT; Mem0/Zep mature"),
    ("Scientific sim / HPC ensembles", 1, 3, 3, 3, 2, "DELEGATE", False, "CMIP6 30 PB", "per-member dense -> Zarr/zfp"),
    ("Autonomous driving datasets", 3, 3, 3, 3, 2, "DELEGATE", False, "Waymo 2 TB", "sensor signal -> codecs; sidecars mature"),
    ("Time-series / IoT", 2, 2, 2, 3, 1, "DELEGATE", False, "1-50 TB/day", "Gorilla codec owns the signal"),
    ("RLHF / preference data", 1, 3, 3, 1, 2, "NO", False, "MB-GB text", "substrate = label order; payload IS the point"),
    ("Distributed tracing", 1, 2, 1, 3, 2, "ANCHOR", True, "TB/day", "many distinct traces; Tempo mature"),
    ("3D scenes / glTF (LOD)", 1, 1, 1, 2, 2, "DELEGATE", False, "MB-TB", "geometry -> Draco/Nanite; LOD = dup copies"),
    ("Vector DBs / embeddings *", 0, 2, 2, 1, 0, "DELEGATE", False, "TB", "control: vectors ARE payload; PQ/HNSW own it"),
    ("Image / audio codecs *", 0, 1, 1, 2, 0, "DELEGATE", False, "exabytes", "control: signal IS payload; codecs irreducible"),
]

VCOLOR = {"BUILD": "#2e7d32", "ANCHOR": "#1565c0", "DELEGATE": "#ef6c00", "NO": "#c62828"}


def composite(sd, mult, adv, sr, sa) -> float:
    return (W["sd"] * sd + W["mult"] * mult + W["sr"] * sr
            + W["sa"] * sa + W["adv"] * adv) / 3 * 100


def main() -> None:
    scored = []
    for (area, sd, mult, adv, sr, sa, verdict, built, scale, note) in ROWS:
        scored.append({
            "area": area, "c": round(composite(sd, mult, adv, sr, sa), 1),
            "verdict": verdict, "built": built, "scale": scale, "note": note,
            "sd": sd, "mult": mult, "adv": adv, "sr": sr, "sa": sa,
        })
    scored.sort(key=lambda r: r["c"], reverse=True)

    # ---- chart ----
    fig, ax = plt.subplots(figsize=(11, 8))
    ys = range(len(scored))
    labels = [f"{'★ ' if r['built'] else ''}{r['area']}" for r in scored]
    ax.barh(list(ys), [r["c"] for r in scored],
            color=[VCOLOR[r["verdict"]] for r in scored], height=.7)
    for y, r in zip(ys, scored):
        ax.text(r["c"] + 0.8, y, f"{r['c']:.0f}  ·  {r['verdict']}", va="center",
                fontsize=8.5, fontweight="bold", color=VCOLOR[r["verdict"]])
    ax.set_yticks(list(ys)); ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis(); ax.set_xlim(0, 118)
    ax.set_xlabel("BH-shape composite score (0-100)  ·  weighted: substrate-dominance .30, "
                  "multiplicity .20, selective-read .20, structural .15, adversarial .15", fontsize=8.5)
    ax.set_title("BH applicability sweep — 20 domains, research-grounded\n"
                 "composite = how BH-shaped · color = verdict (novelty vs already-SOTA)",
                 fontweight="bold", fontsize=12, pad=12)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in VCOLOR.values()]
    ax.legend(handles, [f"{k} — {('greenfield' if k=='BUILD' else 'already SOTA' if k=='ANCHOR' else 'call a codec' if k=='DELEGATE' else 'no fit')}"
                        for k in VCOLOR], loc="lower right", fontsize=8.5, framealpha=.95)
    ax.text(0.5, -0.085, "★ = prototype already built in this repo  ·  * = control domain (should sit low)",
            transform=ax.transAxes, ha="center", fontsize=8, color="#555")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "applicability_map.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # ---- report ----
    L = ["# BH Applicability Scorecard — research-grounded sweep of 20 domains\n"]
    L.append("> Method: one web-grounded research agent per domain gathered real data "
             "volumes, the tools used today, and whether interpretations conflict; each "
             "scored 0-3 on five criteria. The **composite** below is computed from those "
             "scores with declared weights (transparent, reproducible in `scorecard.py`). "
             "Scores are research-informed estimates, not market data.\n")
    L.append("![map](applicability_map.png)\n")
    L.append("**Read it in two axes:** the *composite* says how **BH-shaped** a domain is "
             "(substrate + many layers + selective read). The *verdict* says whether there "
             "is **novel work to do** — because being BH-shaped is not enough if the "
             "store-once + selective-read pattern is already mature SOTA.\n")
    L.append("| # | domain | composite | verdict | scale | why |")
    L.append("|---|---|---|---|---|---|")
    for i, r in enumerate(scored, 1):
        star = " ★" if r["built"] else ""
        L.append(f"| {i} | {r['area']}{star} | **{r['c']:.0f}** | {r['verdict']} | "
                 f"{r['scale']} | {r['note']} |")
    L.append("\n★ = prototype already built in this repo (bhmem / bhtrace / bhckpt / bhanno).\n")
    L.append("## The honest finding\n")
    L.append("1. **Most domains score HIGH (90-100) — and most are `ANCHOR`.** The BH shape "
             "is everywhere, but *store-the-substrate-once + selective-read* is already "
             "mature production SOTA almost everywhere it matters: DICOM (medical), "
             "COG+STAC (satellite/GIS), lakeFS/DVC (data lakes), CRAM+tabix (genomics), "
             "MAM (video), Relativity (legal), named graphs (KGs), S-LoRA (checkpoints). "
             "BH earns **credibility by analogy** there, not a novel build.")
    L.append("2. **Exactly one domain is a clean `BUILD`: CAD/BIM (90).** The research found "
             "no mainstream tool that stores ONE canonical building substrate once with "
             "many additive AND rival discipline/version overlays co-registered as "
             "first-class layers with selective branch/region reads — today federation "
             "*duplicates* and treats clashes as ad-hoc. That union is the gap.")
    L.append("3. **The recurring novel slice is the *rival* layer, not the *shared* one.** "
             "Across annotation, MAM, eDiscovery, genomics and KGs, existing tools store the "
             "substrate once but treat **conflicting interpretations as noise to adjudicate "
             "into one ground truth** — not as first-class, queryable, co-registered rival "
             "layers. That is precisely what `bhanno` models. So BH's genuinely novel "
             "contribution is **narrower and sharper** than 'a universal format': it is the "
             "**first-class representation of adversarial interpretations**.")
    L.append("4. **Our four built prototypes all land `ANCHOR`.** They proved the "
             "*generalization* (one envelope, many domains) honestly — but the sweep shows "
             "their economic win is largely already-solved. That is the method working: it "
             "refuses to let us overclaim.")
    L.append("5. **Controls behaved.** Image/audio codecs (25) and vector DBs (30) sit at "
             "the bottom as `DELEGATE` — the score discriminates dense-signal from "
             "structure-dominant.")
    L.append("\n## Recommendation\n")
    L.append("The one **measured test worth building** is the genuine greenfield: **CAD/BIM** "
             "— a `.bh` where the building object-graph is the substrate, with rival "
             "discipline/version overlays + clash annotations co-registered, selective "
             "branch reads, and the adjudication face. It is the only domain where BH is "
             "*not* re-deriving an existing SOTA pattern.")

    (OUT / "APPLICABILITY_SCORECARD.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print("ranked:")
    for i, r in enumerate(scored, 1):
        print(f"  {i:2d}. {r['c']:5.1f}  {r['verdict']:8s} {'*' if r['built'] else ' '} {r['area']}")
    print(f"\nwrote APPLICABILITY_SCORECARD.md + applicability_map.png")


if __name__ == "__main__":
    main()
