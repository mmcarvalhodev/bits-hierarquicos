# Hierarchical Bits — Presentation Pitch

> **In one sentence:** a representation model where multiple — possibly
> contradictory — interpretations share one immutable substrate and stay
> queryable, without duplicating the data and without forcing them into a single
> truth.

---

## SLIDE 1 — The problem

> **Don't duplicate the world every time someone disagrees with it.**

Start from a common base — one dataset, one building, one document set, one
conversation history. Over that base, multiple interpretations naturally arise:
annotators label it, disciplines read it differently, hypotheses compete over it,
versions accumulate. They **coexist**.

Today, holding them forces a bad choice:

- **copy the base** once per interpretation → K readings cost K copies of the
  world; or
- **merge to one** → a dominant representation wins and the rest is lost.

---

## SLIDE 2 — The idea (a model, not a file format)

> **BH is a representation model for shared immutable substrates and concurrent
> interpretations.**

One substrate, stored once and immutable. Each interpretation is a **first-class,
co-registered entity** over it. The reader picks the lens at read time —
adjudication is deferred and optional, never baked in.

```
SUBSTRATE   stored once, immutable, shared by every reading
LAYERS      each interpretation is a first-class, co-registered entity
READINGS    one lens / the matrix / the majority / the disagreement
            — your choice, at read time, not baked in
```

We give this property a **working name — the First-Class Interpretation
Representation (FCIR)**: interpretations kept as persistent, addressable,
*first-class* entities over a shared substrate, rather than temporary versions or
conflicts to be resolved away. *(Working name — see Slide 4.)*

---

## SLIDE 3 — The distinguishing test (falsifiable)

> Given two interpretations that **disagree** about the same element — can
> **both remain**, neither marked wrong, until a reader chooses (or declines) to
> adjudicate?

Many systems end up **converging to a dominant representation**, or **isolating
each interpretation into an independent copy/version**. BH keeps them
co-registered over one substrate and lets adjudication wait. That is the
differentiator — stated as a test you can run on any system, not a boast.

---

## SLIDE 4 — What we are NOT (the honest positioning)

We surveyed 20 data domains. The result killed the easy claim that "BH is
universally new":

> **Storing the substrate once + reading it selectively is already mature SOTA**
> — DICOM, COG/STAC, lakeFS, CRAM/tabix, S-LoRA, MAM. BH does **not** claim to
> invent that.

Our 20-domain sweep **identified the First-Class Interpretation Representation
(FCIR)** — keeping rival readings as preserved entities instead of resolving them
away — as the property that best distinguishes BH **from the approaches
evaluated**. That is a result of the investigation, not a universal claim; FCIR
is a working name, and the property may yet prove broader. Saying plainly what BH
is *not* — and how far the claim reaches — is what survives the skeptical engineer.

---

## SLIDE 5 — Where it fits, and where it doesn't (the useful limit)

```
FITS     multiple readings of ONE base object:
         · annotation with annotators who disagree
         · agent memory with conflicting versions over one history
         · BIM/CAD — disciplines reading one building (not five copies)
         · legal / eDiscovery — rival readings of one document set
         · science — competing hypotheses over the same raw data

DOESN'T  dense signal (photo / audio / embeddings) → delegate to codecs
         single-truth goals (consensus, gold labels) → already solved
```

A pitch that states its own limit is the opposite of vapor.

---

## SLIDE 6 — The evidence (the principle is reproducible)

The same model showed up — independently — in four completely different domains.
That **reproducibility** matters more than any single number:

| instance | domain | the same model, instantiated |
|---|---|---|
| `bhanno` | rival annotations | the purest: K labelings coexist, adjudication optional |
| `bhmem` | agent memory | conflicting versions over one history |
| `bhckpt` | model checkpoints | alternative readings of one shared base |
| `bhtrace` | traces | competing lenses over one span tree |

One principle, four instances, each measured and tested — correctness as a gate,
honest baselines, public self-corrections, a Zenodo DOI. The numbers exist
(4.6×, 35×, 1,779×, 9×); the point is that the **principle held every time**.

---

## SLIDE 7 — The state and the ask

- **It is a principle with measured instances**, not a finished product. The
  sweep found its **useful limit** — and a useful limit is where a serious
  product starts; without one, it's religion.
- **The next question is product, not novelty:** of the domains where it fits,
  which is the first seed worth building for real?

---

> **Don't duplicate the world every time someone disagrees with it.**
