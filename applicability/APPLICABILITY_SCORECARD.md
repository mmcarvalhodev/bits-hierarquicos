# BH Applicability Scorecard — research-grounded sweep of 20 domains

> Method: one web-grounded research agent per domain gathered real data volumes, the tools used today, and whether interpretations conflict; each scored 0-3 on five criteria. The **composite** below is computed from those scores with declared weights (transparent, reproducible in `scorecard.py`). Scores are research-informed estimates, not market data.

![map](applicability_map.png)

**Read it in two axes:** the *composite* says how **BH-shaped** a domain is (substrate + many layers + selective read). The *verdict* says whether there is **novel work to do** — because being BH-shaped is not enough if the store-once + selective-read pattern is already mature SOTA.

| # | domain | composite | verdict | scale | why |
|---|---|---|---|---|---|
| 1 | Knowledge graphs (multi-ontology) | **100** | ANCHOR | 16B triples | named graphs + RDF-star already SOTA |
| 2 | Medical imaging (multi-reader) | **95** | ANCHOR | WSI 1-100 GB | DICOM SEG references source — mature |
| 3 | Earth obs / satellite | **95** | ANCHOR | 10+ PB | COG + STAC already do it |
| 4 | Legal eDiscovery | **95** | ANCHOR | TB / matter | Relativity store-once + coding fields |
| 5 | Video archives / MAM | **95** | ANCHOR | PB masters | MAM timecoded tracks — mature |
| 6 | Dataset versioning / data lakes | **95** | ANCHOR | PB | lakeFS/DVC zero-copy IS the win |
| 7 | Autonomous driving datasets | **95** | DELEGATE | Waymo 2 TB | sensor signal -> codecs; sidecars mature |
| 8 | Data labeling / annotation ★ | **93** | ANCHOR | COCO 20 GB | CVAT/Label Studio store-once — mature |
| 9 | Genomics (variant calling) | **93** | ANCHOR | ref 3 Gbp | CRAM + tabix selective — mature |
| 10 | Geospatial map tiles | **90** | ANCHOR | PB | COG/PMTiles/vector tiles — mature |
| 11 | CAD / BIM | **90** | BUILD | tens of GB | federation duplicates; rival overlays UNSERVED |
| 12 | Model checkpoints / MoE ★ | **85** | ANCHOR | base GB-TB | S-LoRA / Punica already SOTA |
| 13 | Agent memory ★ | **75** | ANCHOR | KB-MB text | substrate LIGHT; Mem0/Zep mature |
| 14 | Scientific sim / HPC ensembles | **75** | DELEGATE | CMIP6 30 PB | per-member dense -> Zarr/zfp |
| 15 | Time-series / IoT | **68** | DELEGATE | 1-50 TB/day | Gorilla codec owns the signal |
| 16 | RLHF / preference data | **62** | NO | MB-GB text | substrate = label order; payload IS the point |
| 17 | Distributed tracing ★ | **58** | ANCHOR | TB/day | many distinct traces; Tempo mature |
| 18 | 3D scenes / glTF (LOD) | **45** | DELEGATE | MB-TB | geometry -> Draco/Nanite; LOD = dup copies |
| 19 | Vector DBs / embeddings * | **30** | DELEGATE | TB | control: vectors ARE payload; PQ/HNSW own it |
| 20 | Image / audio codecs * | **25** | DELEGATE | exabytes | control: signal IS payload; codecs irreducible |

★ = prototype already built in this repo (bhmem / bhtrace / bhckpt / bhanno).

## The honest finding

1. **Most domains score HIGH (90-100) — and most are `ANCHOR`.** The BH shape is everywhere, but *store-the-substrate-once + selective-read* is already mature production SOTA almost everywhere it matters: DICOM (medical), COG+STAC (satellite/GIS), lakeFS/DVC (data lakes), CRAM+tabix (genomics), MAM (video), Relativity (legal), named graphs (KGs), S-LoRA (checkpoints). BH earns **credibility by analogy** there, not a novel build.
2. **Exactly one domain is a clean `BUILD`: CAD/BIM (90).** The research found no mainstream tool that stores ONE canonical building substrate once with many additive AND rival discipline/version overlays co-registered as first-class layers with selective branch/region reads — today federation *duplicates* and treats clashes as ad-hoc. That union is the gap.
3. **The recurring novel slice is the *rival* layer, not the *shared* one.** Across annotation, MAM, eDiscovery, genomics and KGs, existing tools store the substrate once but treat **conflicting interpretations as noise to adjudicate into one ground truth** — not as first-class, queryable, co-registered rival layers. That is precisely what `bhanno` models. So BH's genuinely novel contribution is **narrower and sharper** than 'a universal format': it is the **first-class representation of adversarial interpretations**.
4. **Our four built prototypes all land `ANCHOR`.** They proved the *generalization* (one envelope, many domains) honestly — but the sweep shows their economic win is largely already-solved. That is the method working: it refuses to let us overclaim.
5. **Controls behaved.** Image/audio codecs (25) and vector DBs (30) sit at the bottom as `DELEGATE` — the score discriminates dense-signal from structure-dominant.

## Recommendation

The one **measured test worth building** is the genuine greenfield: **CAD/BIM** — a `.bh` where the building object-graph is the substrate, with rival discipline/version overlays + clash annotations co-registered, selective branch reads, and the adjudication face. It is the only domain where BH is *not* re-deriving an existing SOTA pattern.
