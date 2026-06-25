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
