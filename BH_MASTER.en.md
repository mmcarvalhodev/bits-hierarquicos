# HIERARCHICAL BITS — TECHNICAL STUDY AND DEMONSTRATION
## A structural envelope that orchestrates representations: method, measurements and boundaries

**Author:** Márcio M. Carvalho
**Study period:** December 2025 – June 2026
**Reference hardware:** NVIDIA GeForce RTX 3060 12 GB · Python 3.13 · NumPy · CuPy/CUDA · Pillow
**Test coverage:** 128+ automated tests green, exact correctness as a gate before every measurement
**Nature of this document:** technical demonstration report — every claim is accompanied by the method and the measured number
**Revision:** v2 (June 2026) — adds three usable prototypes (agent memory, observability, model checkpoints) in §10

---

## EXECUTIVE SUMMARY

Hierarchical Bits (BH) began as a hypothesis from December 2025 ("the byte
is an implicit tree; hierarchy is interpretation"). This study tested the
hypothesis from **nine independent angles**, with real measurements and honest
baselines. The result is not "a better codec" — it is the precise delimitation of a
paradigm:

```
BH does NOT compress dense signal better than JPEG/WebP/AVIF (it loses — measured).
BH IS a STRUCTURAL ENVELOPE that:
   (a) makes the structure explicit at low cost (0–6% of the file — measured),
   (b) routes each region's residual to the right specialist (orchestration),
   (c) offers multiple reads over the same structure (preview/ROI/proof).
```

**Anchor result (measured):** a structured document written in the orchestrated
format is **2.1× smaller than WebP AND** lets you read any region in
**3–55× fewer bytes**, within the same file — something no SOTA tool
offers together.

**The transversal law (measured across all angles):** BH pays off exactly to the
extent that the data is **structure** (rule-generated, composite, hierarchical)
and not **signal** (noise/perceptual). At the limit, the payload becomes a *program* that
generates the data (gains of thousands×); the boundary is not entropy — it is
structure recognition.

---

## 1. METHODOLOGY (what makes this study trustworthy)

The entire investigation followed four rules, applied without exception:

**1.1 Declare before measuring.** Each terrain defined falsifiable claims
with a criterion for **success AND failure** BEFORE the measurement. No number was
promised a priori.

**1.2 Correctness as a gate.** Before any performance comparison, exact
correctness was verified (bit-for-bit reconstruction, equality of aggregates,
valid cryptographic proof). Performance is only measured over a correct result.

**1.3 Honest baseline, with the vs-naive / vs-SOTA distinction.** Large numbers
against naive baselines (full scan, transmitting everything) are marked
as such and distinguished from gains against the state of the art (WebP, HNSW, OLAP).

**1.4 Real measurement, public self-correction.** Real hardware was used (RTX 3060,
CUDA events, `nvidia-smi dmon`). When a measurement was biased in favor of the
hypothesis, it was corrected in public. Three material self-corrections occurred and
are documented (§7) — they are part of the evidence of rigor.

---

## 2. REFRAMING THE QUESTION

The initial question — **"is BH a better codec?"** — was answered, measurement
after measurement, with **no**. The right question only emerged at the end of the investigation:
**"is BH a structural orchestrator of representations?"** — and the answer is
**yes**. The key was a separation that resolves the confusion of half the study:

```
RESIDUAL PROBLEM  ≠  PARADIGM PROBLEM
```

Trying to compress the residual (dense signal) is the problem of specialist codecs
— and BH loses at it. The BH paradigm is structure, belonging and
reads. Separated, each half has an honest and opposite verdict.

---

## 3. THE TERRAINS TESTED (method + measurement)

### 3.1 Image codec — BH as a compressor (loses)

**Method:** quadtree codec with per-node interpretation selection
(LEAF/RAMP/DCT), compared against PNG/JPEG/WebP on 4K frames, with matched PSNR.

**Measurements:**
- Matched content (gradient, lossy): BH-ramp **2.4 KB @ 57.9 dB** vs WebP
  **116.7 KB @ 50.2 dB** → **48× smaller, with higher quality**.
- Access (thumbnail of a natural 4K photo): BH reads **0.148 MB** vs WebP 0.664 (4×),
  JPEG 1.0 (7×), PNG 6.5 (44×).
- Natural photo compression: **loses** (4–10× larger than WebP).
- v0.3 (DCT interpretation): switching the error criterion from L∞ to L2 unlocked the
  DCT and cut 40–66%, but **did not close the gap** — residual entropy coding is missing.
- Heterogeneous image (pure BH-compressor): **loses at all photo fractions
  (10.75× at 0% photo)** — because text/UI explodes the quadtree and WebP's entropy
  coding already makes the easy regions cheap.

**Terrain conclusion:** as a compressor, BH loses. The 48× gain on the
gradient was a corner case (perfectly procedural content), not the rule.

### 3.2 Database — selective read by aggregation

**Method:** aggregation tree (min/max/sum/count per node) over 1,000,000
rows; metric = rows read; baseline = flat scan.

**Measurements:**

| query | BH reads | flat reads | gain | vs |
|---|---|---|---|---|
| global SUM | 0 | 1,000,000 | ∞ | naive |
| SUM range 10% | 1,564 | 99,868 | 64× | naive |
| COUNT key 2% | 2,048 | 1,000,000 | 488× | naive |
| COUNT correlated value > p99 | 92,736 | 1,000,000 | 11× | naive |
| wrong axis / independent value / low selectivity | ~10⁶ | 10⁶ | 1–2× | boundary |

**Interpretation materialization:** a per-region filter (not aggregated) read
everything (1×); with a per-region counter in the node → root read, **0 rows (∞)**
— at the cost of storage that scales with cardinality.

**Honesty:** the gains are enormous vs naive scan, but the mechanism
(pre-computed summary) is already state of the art (zone-maps, OLAP, materialized views).

### 3.3 Verification / Merkle — selective proof

**Method:** Merkle tree (SHA-256, domain separation) over 1,048,576
items; crypto correctness gate (valid proof verifies, forged proof fails) before
measuring; metric = bytes/nodes.

**Measurements:**

| task | BH reads | naive baseline | gain |
|---|---|---|---|
| commitment of 1M items | 32 B (1 hash) | 33.5 MB | 1,048,576× |
| membership proof | 644 B (20 hashes) | 33.5 MB | 52,103× |
| locate tampering | 40 nodes | 1,048,576 re-hashes | 26,214× |

The proof grows with **log n** (1k → 10 hashes; 1M → 20). Honesty: it is the
standard Merkle construction (blockchain/git/CT); the study shows the **unification**
with the other terrains, it does not invent crypto.

### 3.4 Wafer — multiple co-registered layers + scale (film)

**Method:** quadtree-union over co-registered layers (RGB+depth+
segmentation); per-layer lossless reconstruction gate; measurement of
shared-structure vs K independent trees.

**Measurements:**
- Rigid union: co-registered **1.12×**; misaligned **0.32× (loses)**;
  photo+lum+seg **0.67× (loses)**.
- With a derived layer (luminance from RGB): **0.78×**.
- With base + local refinement (non-union): **1.12× (wins)** — the natural photo
  moves from loss to gain; verified by lossless reconstruction.
- **Scale proof (film, 720 frames = 30s):** independent 1.00× · temporal
  (delta between frames) 1.65× · wafer-still 1.12× · **wafer+temporal 2.13×**. The
  structure-fraction rises from **16.7% → 33.4%** with the temporal — structure only
  starts to pay off when redundancy empties the payload.

### 3.5 GPU — data movement (read face, on real silicon)

**Method:** data-movement measurement (simulation) and real wall time
(CUDA events, RTX 3060), with the load visible via `nvidia-smi dmon`.

**Measurements:**
- Simulation (bytes moved, aggregation/LOD/context load): **1,540× less data**.
- Light real test (1 GB in VRAM): total reduction flat 2,991 µs vs BH 2.8 µs →
  **1,087×**; range aggregation **264×**; flat bandwidth **342 GB/s** (pinned at the
  ceiling of 360 → genuinely bandwidth-bound).
- **Heavy test (real load):** 6,000 queries, **3.51 TB scanned**, SM at
  100% for 26 s. Diagnosis of two pitfalls: (a) my flat kernel was
  suboptimal (134 GB/s = 37% of the ceiling), inflating the raw number (4,725×); (b) the
  BH side at the measurement floor (noise). **Honest triangulated number** (time vs
  flat-ideal AND data-moved: 3.51 TB vs ~2 GB): **~1,750×**.

**Extrapolation (published bandwidth, NOT measured):** the batch gain is **hardware-
invariant** (~1,755× from the 3060 to the B200 — algorithmic, both scale with bandwidth);
the single-query gain **shrinks** on fast cards (992× → 45×), because the
kernel-launch floor is fixed.

**Native hardware model (labeled projection, not measurement):** with the floor at
memory-latency level (0.3 µs, physical) instead of launch (2.8 µs,
software): single latency **9,747×**, batch **5,702×** (near-memory build),
energy **~1,755× less** (∝ data moved — robust, independent of the pJ/B value).

**Honesty:** the large numbers are vs naive scan; the mechanism
(pre-computed aggregate) is standard technique (OLAP/materialized views). The GPU proves
that the **read face** is real and fast in hardware; it is not a standalone product.

### 3.6 AI multimodal storage — where BH was tested away from home

**Method:** unified substrate (structure + embeddings) vs stitched stack
(storage + HNSW + cache + spatial index), over a co-registered asset.

**Measurements (storage, slice 1):**

| d (embedding) | unified vs stitched |
|---|---|
| 8 | 4.0× (wins) |
| 128 | tie |
| 256 | 0.86× (loses) |
| **768–4096 (real AI)** | **loses** |

**Self-correction (progressive embedding / Matryoshka):** by treating the embedding
as compressible infrastructure (not irreducible payload) — prefix in the internal
node instead of full-d — the verdict **moves**: d=256 → 1.06×, d=1024 → 1.02×,
d=4096 → 1.00× (ties). The bulk (leaf embedding) is a Shannon tie; the
gain is in the index.

**Measurements (access, slice 2):** preview 7.6× · aggregate 3.2× · ROI 2.1× ·
narrow-scoped retrieval 1.4× · **broad retrieval 0.23× (loses)**.

**Architectural debt decomposition (real RAG stack):** the eliminable debt
is **14–49%** (borderline), **dominated by embedding duplication** (dense
payload), not by structure. Conclusion: dense AI storage is not BH's terrain.

### 3.7 Compositional / real density — the strongest signal and its limit

**Method (compositional):** symbolic data — concepts as equations of
shared primitives — represented as an algebraic envelope vs dense vector.

**Measurement:** **384× smaller** (8 MB vs 3.07 GB for 1M concepts), and it answers
structural queries ("which concepts use primitive X?") that the dense vector
**cannot even formulate**.

**Method (real density):** intrinsic dimensionality of real embeddings
(all-MiniLM-L6-v2 model, 6,000 PT words, PCA).

**Measurement:** 90% of variance in **160 of 384 dimensions** (~2.4× compressible).
**Honesty:** this is *linear* compressibility (already exploited by PCA/PQ/
Matryoshka), **not** symbolic compositionality. Real language data,
in embedding geometry, is **not** compositional-symbolic — it is a subspace
of medium dimension. The 384× holds for data *that is* composition; how much of the
real world is compositional remains the open bet (of the symbolic domain).

### 3.8 Decode-program — payload becomes program (the deep form of the law)

**Method:** the header carries the *program* that generates the region (not the
result); the decoder executes the program. Test of generality (several
families) + noise + hidden cost.

**Measurements:**

| rule-generated family | WebP | program | gain |
|---|---|---|---|
| rings | 37.8 KB | 13 B | 2,904× |
| waves | 46.4 KB | 13 B | 3,572× |
| checkerboard | 2.4 KB | 3 B | 809× |
| gradient | 2.1 KB | 1 B | 2,096× |

**Under noise** (procedural base + noise α): the program-aware approach **keeps the
structure advantage** at all noise levels (subtracts the known base; whole-WebP
pays for the structure it cannot separate). **Hidden cost (declared):** the
encoder needs to **discover** the program — the inverse problem, trivial for a
known family, **undecidable in general** (Kolmogorov complexity is
uncomputable). BH's boundary is not the residual's entropy — it is
**structure recognition**.

### 3.9 Orchestration + union — the formulation that wins for the right reason

**Method (orchestration):** BH routes each region to the local specialist
(flat→constant, gradient→formula, text→PNG, photo→WebP), compared against
one-codec-on-the-whole, on two content types.

**Measurements:**

| content | whole-WebP | orchestrated | result |
|---|---|---|---|
| photo-heavy | 10.7 KB | 10.8 KB | 1.01× (ties) |
| **document (closed forms)** | 4.8 KB | **2.2 KB** | **2.1× smaller** |

Splitting into WebP per region (without routing paradigms) **loses** (1.10×) — the gain
comes from cross-paradigm routing, not from the cut.

**Method (envelope cost):** decomposition of BH's bytes into framing /
explicit structure / residual. **Measurement:** explicit structure = **0–6% of the
total** (3 images). The smart header is cheap; the expensive part was the residual
(now delegated). *Answers the "killer question": making the structure
explicit costs very little.*

**Method (the union):** document written as `.bh`, measuring the two faces in
the same file.

**Measurements:**
- Representation: **2.3 KB vs 4.8 KB for WebP = 2.1× smaller**.
- Selective read: reading 1 region costs flat 87 B · gradient 96 B · text
  590 B · diagram 1.8 KB — **3 to 55× less** than WebP, which needs the whole
  file for any region.

```
WebP/AVIF → optimal residual, SINGLE read
PDF       → orchestrates specialists, but flat list, no selective read
OLAP/GPU  → selective read, but not a representation format
.bh       → BOTH faces + hierarchy + belonging, in a single envelope
```

---

## 4. THE TRANSVERSAL LAW (measured across all angles)

```
Hierarchy pays off when STRUCTURE dominates the cost, not dense SIGNAL.
At the limit: payload → PROGRAM that generates the data, to the extent that the data is
rule-generated. The boundary is not entropy — it is structure recognition.
```

| data class | measured result |
|---|---|
| procedural / formula | tiny program: 800–3,600× (decode-program) |
| compositional / symbolic | envelope 384× smaller + queries the dense one cannot do |
| heterogeneous structured | orchestration 2.1× + selective read 3–55× |
| aggregable / reused | selective read ∞–488× (database), 1,750× (GPU) |
| co-registered + redundant | wafer+temporal 2.13× (film) |
| **dense / perceptual (photo, audio, embedding)** | **loses or ties — connectionism's territory** |

---

## 5. THE REORGANIZED THESIS (supported by the evidence)

**BH is not a codec — it is a structural orchestrator.** Two faces, measured:

- **Read face** (summary in the node → reading selectively is cheap): GPU 1,750×,
  database ∞/488×, Merkle 52,000×, thumbnail/ROI 4–44×. Enormous numbers, but the
  mechanism is already SOTA.
- **Representation face** (explicit structure + delegated residual):
  orchestration 2.1× on a document. Smaller number, but **vs the state of the art**, by
  an architectural property.

**The union** of the two faces in one envelope (2.1× smaller AND navigable) is what no
SOTA tool delivers. **The value is not in the compressed block — it is in the
structure that knows what that block means.**

**Three scales where BH survives scrutiny:**
1. structural format (one asset) · 2. orchestrator (heterogeneous asset) ·
3. compositional substrate (symbolic system). Common root: structure > signal.

---

## 6. HONEST BOUNDARIES (so the thesis does not turn into faith)

```
- "Wins for the right reason" ≠ "we found the product". It is scientific validation; the
  product requires construction and adoption (engineering, not benchmark).
- The orchestrator competes with PDF (the incumbent), not with WebP. Its differentiator
  — hierarchy + multiple reads — is real but unproven as a market need.
- The large numbers of the read face are vs NAIVE; vs SOTA, they tie. The
  differentiator is the UNION of the faces, not an isolated number.
- The decode-program requires RECOGNIZING the structure (inverse problem): trivial for
  a known family, undecidable in general.
- BH's home is STRUCTURE-DOMINANT data; in dense signal connectionism reigns,
  and BH DELEGATES to it — it does not confront it.
- A format dies without an ecosystem. The path is not a generic `.bh` competing
  with Parquet/PDF; it is building it native in a greenfield domain that already needs it.
```

---

## 7. THE SELF-CORRECTIONS (evidence of rigor, not of weakness)

Three measurements were corrected in public when they proved to be biased:

1. **GPU — suboptimal flat kernel.** The raw number (4,725×) was inflated by a poor
   baseline implementation; the honest triangulated number is ~1,750×.
2. **Multimodal — embedding treated as irreducible payload.** Corrected with
   progressive representation (Matryoshka): storage moved from "loses" to "ties".
3. **Heterogeneous — hypothesis "wins on mixed content".** Refuted by the number
   (loses 10.75×); the real gain requires per-specialist routing (orchestration),
   not pure BH-compressor.

---

## 8. RELATED WORK (situating vs the state of the art)

BH does not invent the techniques it uses — it **unifies** them. Each isolated
capability already exists and is mature; the contribution is to bring them together in a single
structural envelope. We situate here the four families of prior art.

**Adaptive per-block codecs.** JPEG (Wallace, 1991) established the model
"transform + quantization + entropy coding" with a fixed global basis (DCT).
Modern codecs — AV1/AOMedia (Chen et al., 2018), VVC, JPEG XL — do
*mode decision* per block, choosing prediction/transform modes per
region. The BH-codec competes directly here and **loses** (§3.1): it lacks the
entropy-coding machinery, and per-region selection is what AV1 already does. The
difference of BH is not compression — it is delegating the region to the specialist (§3.9).

**Selective-read structures.** The "read the summary, not the data" read is
the basis of OLAP/data cubes (Gray et al., 1997), zone-maps and per-
row-group statistics in Apache Parquet, and *materialized views*. The gains of §3.2 and §3.5
(database, GPU) are exactly this mechanism — enormous against naive scan,
but **already state of the art**. We recognize them as a credibility anchor, not
novelty.

**Authenticated structures.** The verification face (§3.3) is the Merkle
tree (Merkle, 1987), the basis of Git, Certificate Transparency (Laurie, 2014)
and blockchains (Nakamoto, 2008). We do not invent crypto; we demonstrate that the
Merkle-proof is the *same* read-by-objective-over-hierarchy as the other
terrains.

**Compact representation and data-as-program.** For embeddings, the
compressibility that §3.6/§3.7 exploit is Product Quantization (Jégou et al.,
2011) and Matryoshka Representation Learning (Kusupati et al., 2022); vector
search is HNSW (Malkov & Yashunin, 2018). The "decode-program" of §3.8 is the
direction of Kolmogorov complexity (Kolmogorov, 1965; Li & Vitányi) and has
direct precedent in PostScript (page-as-program, Adobe) and procedural
generation. Self-describing formats (HDF5, Protocol Buffers, PDF/ISO 32000)
prove that "data that carries its own structure" works.

**The gap that BH occupies.** None of these unifies representation + selective
read + specialist orchestration + hierarchy/belonging + proofs
in a single envelope. PDF orchestrates but is a flat list without selective read; OLAP
navigates but is not a representation format; AV1 adapts per block but with a single
family of modes. BH's contribution is the **union**, not the components.

---

## 9. REPRODUCTION

```
codec     X:\bitH\           py -m pytest tests -q   ·  src/bench/{harness,headtohead,portfolio,
                              heterogeneous,cost_envelope,orchestrate,union}.py
database  X:\bitH\db\        py -m pytest tests -q   ·  src/bench/harness.py
merkle    X:\bitH\merkle\    py -m pytest tests -q   ·  src/bench/harness.py
wafer     X:\bitH\wafer\     py -m pytest tests -q   ·  src/bench/{harness,film}.py
gpu       X:\bitH\gpu\       py -m pytest tests -q   ·  src/bench/{real_gpu,heavy_gpu,extrapolate,native_model}.py
multimodal X:\bitH\multimodal\  src/{probe,fatia2,probe_progressive}.py
composit.  X:\bitH\compositional\  {probe_compositional,real_density,decode_program,program_test}.py
debt       X:\bitH\architecture_debt\  debt_decomposition.py

Python: X:/miniconda3/python.exe  (NumPy, Pillow, hashlib, CuPy/CUDA, sentence-transformers, sklearn)
Raw reports per terrain: RESULTS_*.md in each folder.
```

---

## 10. CONCLUSION

The study tested Hierarchical Bits from nine independent angles, with a declared
method, correctness as a gate, honest baselines and public self-correction. The
verdict:

> BH is not a better codec — it is a different way to **organize and read
> structured data**. Where the data is structure (rule-generated, composite,
> hierarchical, aggregable, co-registered), the gain is real and sometimes by orders
> of magnitude, and its deepest form is the payload becoming the *program* that
> generates the data. Where the data is dense signal (photo, audio, embedding),
> connectionism reigns, and BH's role is to **delegate** to the specialist — not
> to compete. The unique contribution is not an isolated number; it is the **union**, in a
> single envelope, of lean representation, selective read, hierarchy and
> belonging — which no current tool offers together.

The final proof is not one more benchmark; it is the construction of the format in a domain
where structure and belonging matter as much as size.

### From thesis to artifacts — three usable prototypes

The construction is no longer one step but three, and they share **one
envelope** — proof the paradigm generalizes across domains. Each is a Python
library with a measured demo and tests; each reads only the fraction a query
asks for, in real bytes read from the file.

**`bhmem` — agent memory.** The agent writes structured memories
(fact/event/relation + time + topic + provenance); the format exposes them
through the multiple reads.

| read | what it returns | bytes read | vs flat store (reads all) |
|---|---|---|---|
| `summary()` | summary of all topics | 2.5% | **35× less** |
| `recall(topic)` | the memories of one branch | 4.0% | **22× less** |
| `since(t)` | memories of the temporal window | 9.8% | **9× less** |
| `provenance(id)` | source+path of 1 memory | 10.8% | **8× less** |

*(Demo: ~90 days, 60 topics, 2,250 memories; 9/9 tests green.)*

**`bhtrace` — distributed traces (observability).** A trace is a tree
(trace → spans → events); the structure is the index, the heavy attributes (SQL,
stack traces, headers) are the residual.

| read | what it returns | vs flat store |
|---|---|---|
| `summary()` / `critical_path()` | the skeleton without the payload | **9× less** |
| `subtree(span)` | a drill-in | **9× less** |
| `service(name)` | one service | **5× less** |

*(Demo: 269-span checkout trace, attribute-heavy; 9/9 tests green.)*

**`bhckpt` — model checkpoints.** A checkpoint is a hierarchy
(model → layers → tensors → experts); the weights dominate, the structure is tiny.

| read | what it returns | vs flat checkpoint |
|---|---|---|
| `summary()` | architecture of a 16 MB model read in 9 KB, no weights | **1,779× less** |
| `expert(i, e)` | load one MoE expert without the mixture | **20× less** |
| `layer(i)` / `tensor(name)` | one layer / one tensor | **12× / 10× less** |

*(Demo: 4-layer transformer, 2 MoE layers × 6 experts, 16.2 MB; 8/8 tests green.)*

**Honest boundary, the same across all three:** BH wins on structural access and
**delegates** the dense residual (full-text search → inverted index; per-tensor
quantization → its specialist; dense semantic recall → a vector index). For
`bhckpt`, selective per-tensor read already exists (`safetensors`) — that is the
*anchor*; the new piece is the *union* (hierarchy including the MoE expert as a
first-class read, per-tensor codec routing, a Merkle face for provenance).

These are not more measured angles — they are the thesis turning into tools, the
**same envelope proven in three domains**. The gain scales with how
structure-dominant the data is — the transversal law of §4. See the respective
READMEs (`bhmem/`, `bhtrace/`, `bhckpt/`).

---

*"The value is not in the compressed block. It is in the structure that knows what that
block means."*
