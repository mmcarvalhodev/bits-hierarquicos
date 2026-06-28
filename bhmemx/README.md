# bhmemx — multi-agent memory with preserved disagreement (FCIR 3-4)

> The prototype that exercises the **differentiator** the meta-critique was right
> we had never tested: FCIR **property 3-4** (contradiction preserved + adjudication
> deferred), not 1-2 (selective read). It is the one `BUILD` the
> [property-3-4 re-score](../applicability/RESCORE_FCIR.md) put at the top.

Multiple agents form beliefs about a **shared fact substrate**; on some facts they
**disagree**. Current multi-agent memory systems force consensus and **discard**
the dissent. `bhmemx` keeps every agent's belief first-class and the disagreement
**queryable**.

```python
from bhmemx import Belief, MultiAgentStore, MultiAgentReader

s = MultiAgentStore(["alice", "bob", "carol"])
s.add_fact("door_locked", "is the door locked?")
s.believe(Belief("alice", "door_locked", "true",  confidence=0.9))
s.believe(Belief("bob",   "door_locked", "true",  confidence=0.7))
s.believe(Belief("carol", "door_locked", "false", confidence=0.95))   # dissent — kept
s.save("agents.bmx")

r = MultiAgentReader("agents.bmx")
r.fact_views("door_locked")   # {'alice':'true','bob':'true','carol':'false'}  — the matrix
r.disagreements()             # facts where agents contradict — preserved
r.agent_reliability()         # who dissents from the majority most
r.adjudicate("majority")      # optional, read-time consensus — beliefs untouched
r.adjudicate("weighted")      # different rule, same data, no re-write
```

## What it demonstrates (property 3-4)

- **Computing over disagreement**, not bytes: `fact_views` (the matrix),
  `disagreements`, `agent_reliability`, and `adjudicate(rule)` re-run at read time
  **without destroying** the rival beliefs.
- Demo (4 agents, 40 facts, ~30% contested): the queries return the disagreement
  structure; majority vs confidence-weighted adjudication changes some verdicts —
  computed at read time, the layers unchanged. 7/7 tests green.

## Honest boundary (the same discipline as the rest of the repo)

- **The genuine win vs current multi-agent memory is real:** those systems force
  consensus and throw away the dissent; bhmemx keeps it first-class. That is the
  FCIR stance the re-score flagged as a `BUILD`.
- **But the *capability* ties an uncollapsed `(fact, agent, value)` table** — every
  query here is a `GROUP BY` (measured in
  [`../directions/RESULTS_DISAGREEMENT_COMPUTE.md`](../directions/RESULTS_DISAGREEMENT_COMPUTE.md):
  gold-collapse 0/4, uncollapsed table 4/4). FCIR's delta is the **discipline**
  (do not collapse on write) **+ co-registration** to the shared substrate, not a
  new capability. We state this rather than hide it.

## Run

```
X:/miniconda3/python.exe X:/bitH/bhmemx/demo.py        # -> RESULTS_BHMEMX_DEMO.md
X:/miniconda3/python.exe -m pytest X:/bitH/bhmemx/tests/ -q   # 7/7
```
