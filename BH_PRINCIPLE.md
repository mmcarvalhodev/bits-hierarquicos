# Hierarchical Bits — The Principle
## First-Class Interpretation Representation (FCIR) — a working name

> *From a file format to a property of representation.*

The applicability sweep ([`applicability/`](applicability/)) established something
uncomfortable and clarifying: the BH **shape** — a heavy substrate stored once,
many co-registered layers, selective reads — is **already mature SOTA** in nearly
every domain where it matters (DICOM, COG/STAC, lakeFS, CRAM/tabix, MAM, S-LoRA,
named graphs). Selling BH as "substrate + overlays" is selling something the
world already has.

So the contribution is not the format. It is a **principle** the prototypes are
instances of — and principles survive where formats age.

## The thesis

> **Hierarchical Bits is not a storage format. It is a way of representing data
> in which multiple concurrent — and possibly contradictory — interpretations
> share a single immutable substrate and persist as co-equal, first-class,
> individually addressable entities; adjudication between them is deferred to
> read-time and optional, never baked in and never destructive.**

We give this property a **working name** — the **First-Class Interpretation
Representation (FCIR)**: *a representation in which interpretations are
first-class — persistent, addressable, co-equal — rather than temporary versions
or conflicts to be resolved away.* "First-class" is the load-bearing word: it is
what separates an interpretation with independent standing from one that exists
only until it is merged into a single truth.

**Why "working name."** A property earns a permanent name after it has been
observed, tested, and seen to recur across contexts — not at the moment it is
first noticed. We are at the start of that sequence, not the end. So the honest
statement is not *"BH's contribution is FCIR"* (a universal claim) but:

> **Our investigation identified FCIR as the property that best distinguishes BH
> from the approaches evaluated.**

That is a description of a result, scoped to what we surveyed — not a law, and
not a fence around what BH might later turn out to be. If the property proves
broader or subtly different as it recurs in new contexts, the name should follow
the idea, not constrain it.

![FCIR — the model in one picture: rival interpretations co-registered over one immutable substrate; adjudication is a read-time, optional choice (one lens / majority / keep the disagreement)](pitch_assets/fcir_diagram.svg)

The same model, as text (for readers — human or machine — that don't render SVG):

```
   Interp A (alice):  sky   cat   road    ┐
   Interp B (bob):    sky   cat   road    ├ coexist · co-registered · first-class
   Interp C (carol):  sky   DOG   road    ┘ (they disagree at e₂ — both kept)
                       │     │     │
   substrate:          e₁    e₂    e₃       immutable · stored once
                             │
       read-time adjudication (OPTIONAL · not stored):
          σ one lens   ·   majority → "cat"   ·   ⊥ keep the disagreement
```

### A worked example — 3 annotators, one image

```
Substrate:  image #042  — stored once (the pixels)
Interp A (alice):  { object: "cat" }
Interp B (bob):    { object: "cat" }
Interp C (carol):  { object: "dog" }        ← disagreement, preserved

Reads (all over the one stored image):
  layer("carol")        → { object: "dog" }
  item_views("#042")    → { alice:"cat", bob:"cat", carol:"dog" }   # the matrix
  adjudicate(majority)  → "cat"      # optional, at read time; the layers stay
  disagreements()       → ["#042"]   # found by reading labels only, not the image
```

What FCIR changes vs today: current pipelines collapse A, B, C into a single gold
label and **discard the fact that carol disagreed**. FCIR keeps all three
first-class and lets each consumer adjudicate — or not — at read time. This is
exactly the [`bhanno`](bhanno/) prototype.

## The distinguishing test

What separates a BH representation from an `ANCHOR` system (one that *also*
stores the substrate once and reads it selectively)?

> Given two interpretations that **disagree** about the same element of the
> substrate, can **both remain** — permanently, queryable, neither marked wrong —
> until a reader chooses, or declines, to adjudicate?

- **`ANCHOR` systems answer no.** They converge to one canonical truth: a
  consensus mask, a gold label, a final coding decision, a merged model, a
  resolved clash. Disagreement is a *problem to be resolved* — noise on the way
  to ground truth.
- **BH answers yes.** Disagreement is *data to be preserved*. The rival readings
  coexist as permanent residents; the system never forces one to win by erasing
  another.

That single yes/no is the whole difference.

## The four properties

| # | property | shared with ANCHOR? |
|---|---|---|
| 1 | **Immutable shared substrate** — stored once, referenced by all layers | yes — already SOTA |
| 2 | **Interpretations as first-class entities** — persistent and addressable, not on-the-fly derived views nor mergeable annotations | partly |
| 3 | **Coexistence of contradiction** — rival readings of the *same* element are preserved together, as data | **no — the differentiator** |
| 4 | **Deferred, optional adjudication** — at read time the reader picks a lens: one interpretation / the matrix / the majority / the disagreement | **no — the differentiator** |

Property 1 is the part that is already everywhere. Properties **3 and 4** are
the part the sweep found **still under-explored**: most systems treat rival
interpretations as a mess to clean up, not as co-equal entities to keep.

## How FCIR relates to adjacent systems

A blind read test (five fresh reviewers, three model tiers, README only)
converged on one verdict: the *message* is clear, but the *novelty* is not yet
defended — every reviewer independently named existing systems they believed
already do this. They were right to. Here is the confrontation, under one rule:
**where a system already does exactly this, we say so — no makeup.**

The FCIR property has five parts: (1) one shared, immutable substrate;
(2) interpretations that may **contradict**; (3) kept as first-class,
addressable, co-equal entities; (4) co-registered to the **same substrate
elements**; (5) adjudication **deferred and optional** — neither reading marked
wrong.

| system | satisfies all five? | honest verdict |
|---|---|---|
| **RDF named graphs + PROV** | yes, for triples | **already FCIR, in the triple/KG domain** |
| **Standoff annotation** (W3C Web Annotation, UIMA/GATE) | yes, for text/media | **already FCIR, in the annotation domain** |
| Git / branches | no | defers adjudication, but is built for *eventual merge*; branches are divergent whole-tree states, not co-equal readings co-registered per element |
| Bitemporal DBs / Datomic | partial | immutable + non-destructive history, but *temporal supersession of one truth*, not co-equal **simultaneous** rivals from different interpreters |
| CRDTs | no (opposite intent) | designed to **auto-converge** to one state without coordination; preserving disagreement is exactly what they remove (multi-value registers keep concurrent values only until the app resolves) |
| Event sourcing | no | immutable log + many **derived** projections, but the projections are different shapes of *one* truth, not contradictory rivals |

**The admission, without makeup.** Two of these — **RDF named graphs with
provenance** and **standoff annotation** — already implement the FCIR property in
full, each within its own domain. Our `bhanno` prototype *is* standoff
annotation; it did not invent it. For triple-shaped knowledge, named graphs got
there twenty years ago. **So FCIR is not a new mechanism, and any claim that
"nobody does this" is false.**

**What is left, then — stated at its honest size.** FCIR is an **architectural
synthesis and a name**, not an invention:

1. a **single name** for a property that today exists only in domain-specific
   forms (named graphs for triples, standoff for text) and has *no shared term*
   across images, BIM models, model weights, agent memory;
2. a **falsifiable test** — *can two readings of the same element both remain,
   neither marked wrong, until adjudication is chosen?* — that classifies any
   system in one line;
3. the **observation** that the property recurs across domains that do not talk
   to each other, and that **most** systems in **most** domains do *not* have it
   (they converge, merge, or supersede).

That is a smaller claim than "a new representation paradigm." It may still be
useful — naming a recurring property and giving it a test is how scattered
practice becomes a discussable concept — but it **stands or falls as a
synthesis**, and an honest reader should judge it as one, not as a mechanism that
did not exist before.

### Discipline, not paradigm — naming the contraction

This investigation began with a larger ambition ("not a change of form, a change
of paradigm") and has, under measurement, **contracted to a smaller and firmer
claim** — and that contraction should be named, not left for the reader to infer.

> FCIR is a **well-modeled discipline, not an impossible capability.** Its value
> is **not** "nobody can do this without FCIR" — the
> [disagreement-compute test](directions/RESULTS_DISAGREEMENT_COMPUTE.md) shows
> an uncollapsed `(item, source, value)` table already answers every query a
> `bhmemx`-style store does (4/4). Its value **is**: a single name, a falsifiable
> test, formal operators (`⊕ Δ σ α ▷`), and the **discipline** of *not collapsing
> on write* — given to a practice that industry workflows systematically abandon.

A paradigm breaks when something was **impossible** before and is possible now
(relativity changed the physics). Nothing here was impossible — disagreement was
always a `GROUP BY` away in an uncollapsed table. What is real, and enough for a
contribution, is that the prevailing practice **destroys** that table by default,
and FCIR names, tests, and models the alternative. We claim the discipline; we do
not claim the impossibility.

A **formal algebra** of these operators — coexistence `⊕`, conflict `Δ`,
projection `σ`, adjudication `α`, precedence `▷` — with FCIR stated precisely as
`⊕ ⊥ α` (coexistence decoupled from adjudication), is in
[`BH_ALGEBRA.md`](BH_ALGEBRA.md). It is what answers *"a model, or just a
pattern?"* — as a specification, not yet a verified theory.

## The prototypes are instances, not the point

Each `.bh` prototype is one instance of the principle — and they vary in how
sharply they exercise properties 3–4:

| instance | substrate | rival interpretations | adjudication deferred? |
|---|---|---|---|
| [`bhanno`](bhanno/) | a media item | K annotators that disagree | **yes** — `adjudicate()` is optional; the purest instance |
| [`bhmem`](bhmem/) | the interaction log | conflicting belief/fact versions over time | partial — rival temporal versions kept |
| [`bhckpt`](bhckpt/) | base model weights | adapters / quantizations (alternative, mostly *additive*) | weak — interpretations rarely contradict |
| [`bhtrace`](bhtrace/) | the span tree | competing analysis lenses / root-cause hypotheses | weak — lenses coexist more than contradict |
| `bhbim` (candidate) | the building object-graph | rival discipline/version overlays + clashes | **yes** — the one BUILD domain in the sweep |

The closer an instance sits to "rival readings preserved without forced
adjudication," the more it expresses what is *new* about BH versus the ANCHOR
systems. `bhanno` (and the proposed `bhbim`) are the sharp instances; the others
demonstrate the *generalization* but lean on the already-SOTA substrate-sharing.

## Honest scope

- This is the differential **observed so far, in the 20 domains surveyed** — not
  a closed claim that properties 3–4 are BH's *only* possible value. New domains
  may surface other under-served slices.
- The substrate-sharing economics (property 1) remain real and measured in the
  prototypes — they are just **not novel**. BH's claim there is credibility by
  analogy, not invention.
- "Without forced adjudication" is a *representation* stance, not a truth claim:
  BH surfaces the contest and the majority; it does not decide who is right.
  Resolving truth stays a modeling choice the reader makes, or declines.
- **The optionality can be illusory downstream.** Many consumers need *a single
  resolved value*, not a matrix — so "deferred adjudication" often means "deferred
  to the next system in the pipeline, which then force-adjudicates." FCIR's
  optionality is real *in the store*; whether it survives to the point of use
  depends on whether any downstream consumer is willing to carry the matrix
  instead of demanding a scalar. Where every consumer demands a scalar, FCIR buys
  provenance and auditability, not genuine deferral.
- **It scales in K, but the storage win saturates.** A
  [scaling probe](bhmemx/scale_test.py) (200 facts, K = 3 → 100 agents) shows the
  marginal cost of agent *K+1* is **flat** (~one belief layer; linear, no
  explosion) and read-time compute over the whole matrix stays sub-20 ms at
  K = 100. But the storage saving vs K independent copies *saturates* (≈1.7× →
  2.8×, then flat): once the per-agent layers dominate the shared substrate, the
  "stored once" economy stops growing. The case for FCIR at high K is the
  discipline and the single model — **not** an unbounded storage advantage.

## Why this is the advance

It moves the centre of gravity from the **file** to the **model**. If the thesis
above can be stated precisely — and the distinguishing test makes it falsifiable:
*does this system preserve contradicting interpretations without adjudication, or
not?* — then the value of BH stops depending on any single prototype and starts
depending on the clarity and generality of the principle. The prototypes become
evidence; the principle becomes the contribution.

---

*Companion to [`BH_MASTER.md`](BH_MASTER.md) (the measured study) and
[`applicability/`](applicability/) (the domain sweep). A Portuguese version can
be produced on request.*
