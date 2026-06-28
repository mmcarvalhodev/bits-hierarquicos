# bhmemx — multi-agent memory with preserved disagreement (FCIR 3-4)

- 4 agents · 40 facts · 12 contested

## Computing over disagreement (the property 1-2 prototypes never exercised)

- **`fact_views('f002')`** → {'alice': 'true', 'bob': 'true', 'carol': 'true', 'dave': 'unknown'}  *(the matrix — all kept)*
- **`disagreements()`** → 12 contested facts (e.g. `f002`: majority true, agreement 0.75)
- **`agent_reliability()`** (dissents from majority) → alice:7, dave:6, carol:4, bob:0
- **`adjudicate('majority')` vs `adjudicate('weighted')`** → 5 facts change verdict — *re-adjudicated at read time, the rival beliefs untouched*

## Storage (co-registration — the only 1-2 economics that remains)

- `.bmx` (substrate once + 4 belief layers): **7,664 B** · 4 independent agent copies: 15,837 B → **2.07× smaller**

## Honest boundary

- **This exercises property 3-4** (disagreement preserved + adjudication deferred) — what the earlier prototypes did not. The win vs current multi-agent memory is real: those force consensus and **discard** the dissent; bhmemx keeps it queryable.
- **But the capability ties an uncollapsed `(fact, agent, value)` table** — these queries are GROUP BY (see `../directions/RESULTS_DISAGREEMENT_COMPUTE.md`). FCIR's delta is the **discipline (don't collapse) + co-registration**, not a new capability vs an uncollapsed table. Stated honestly, not hidden.
