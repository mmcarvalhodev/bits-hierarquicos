"""bhmemx demo — multi-agent memory with preserved disagreement (FCIR 3-4).

Four agents observe a shared environment and form beliefs about facts; on some
facts they disagree. Current multi-agent memory systems force consensus and
discard the dissent; bhmemx keeps it first-class and queryable. This demo runs
the disagreement-compute queries (not byte queries — that is the point).

Run: X:/miniconda3/python.exe X:/bitH/bhmemx/demo.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhmemx import Belief, MultiAgentReader, MultiAgentStore  # noqa: E402

OUT = Path(__file__).resolve().parent
AGENTS = ["alice", "bob", "carol", "dave"]
N_FACTS = 40
VALUES = ["true", "false", "unknown"]
rnd = random.Random(0)


def build() -> MultiAgentStore:
    s = MultiAgentStore(AGENTS)
    for i in range(N_FACTS):
        fact = f"f{i:03d}"
        s.add_fact(fact, f"observation #{i} about the shared environment")
        contested = rnd.random() < 0.3          # 30% of facts are contested
        truth = rnd.choice(VALUES)
        for a in AGENTS:
            v = rnd.choice(VALUES) if contested and rnd.random() < 0.6 else truth
            s.believe(Belief(a, fact, v, confidence=round(rnd.uniform(0.5, 1.0), 2), ts=i))
    return s


def main() -> None:
    store = build()
    path = store.save(OUT / "agents.bmx")
    r = MultiAgentReader(path)

    dis = r.disagreements()
    rel = r.agent_reliability()
    maj = r.adjudicate("majority")
    wgt = r.adjudicate("weighted")
    changed = [f for f in maj if maj[f] != wgt[f]]
    sc = r.storage_comparison()

    L = ["# bhmemx — multi-agent memory with preserved disagreement (FCIR 3-4)\n"]
    L.append(f"- {len(AGENTS)} agents · {N_FACTS} facts · {len(dis)} contested\n")
    L.append("## Computing over disagreement (the property 1-2 prototypes never exercised)\n")
    if dis:
        ex = dis[0]
        L.append(f"- **`fact_views('{ex['fact']}')`** → {ex['views']}  *(the matrix — all kept)*")
        L.append(f"- **`disagreements()`** → {len(dis)} contested facts (e.g. `{ex['fact']}`: "
                 f"majority {ex['majority']}, agreement {ex['agreement']})")
    L.append(f"- **`agent_reliability()`** (dissents from majority) → " +
             ", ".join(f"{a}:{n}" for a, n in rel))
    L.append(f"- **`adjudicate('majority')` vs `adjudicate('weighted')`** → {len(changed)} facts "
             "change verdict — *re-adjudicated at read time, the rival beliefs untouched*")
    L.append("")
    L.append("## Storage (co-registration — the only 1-2 economics that remains)\n")
    L.append(f"- `.bmx` (substrate once + {sc['agents']} belief layers): **{sc['bmx_bytes']:,} B** · "
             f"{sc['agents']} independent agent copies: {sc['independent_copies_bytes']:,} B → "
             f"**{sc['saving']}× smaller**")
    L.append("")
    L.append("## Honest boundary\n")
    L.append("- **This exercises property 3-4** (disagreement preserved + adjudication deferred) — "
             "what the earlier prototypes did not. The win vs current multi-agent memory is real: "
             "those force consensus and **discard** the dissent; bhmemx keeps it queryable.")
    L.append("- **But the capability ties an uncollapsed `(fact, agent, value)` table** — these "
             "queries are GROUP BY (see `../directions/RESULTS_DISAGREEMENT_COMPUTE.md`). FCIR's "
             "delta is the **discipline (don't collapse) + co-registration**, not a new "
             "capability vs an uncollapsed table. Stated honestly, not hidden.")

    (OUT / "RESULTS_BHMEMX_DEMO.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"agents={len(AGENTS)} facts={N_FACTS} contested={len(dis)}")
    print(f"  agent_reliability (dissents): " + ", ".join(f"{a}:{n}" for a, n in rel))
    print(f"  majority vs weighted: {len(changed)} verdicts change (read-time, non-destructive)")
    print(f"  storage: {sc['bmx_bytes']}B vs {sc['independent_copies_bytes']}B copies = {sc['saving']}x")
    print(f"report: {OUT/'RESULTS_BHMEMX_DEMO.md'}")


if __name__ == "__main__":
    main()
