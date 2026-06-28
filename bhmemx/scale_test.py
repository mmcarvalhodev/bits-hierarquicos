"""bhmemx scaling probe — answers the open critique: what is the marginal cost
of agent K+1, and does FCIR stop being viable at high K?

We hold the substrate fixed (F facts) and grow K (agents), each believing every
fact (worst case for layer bytes). We measure, per K:

    bmx_bytes              the single co-registered store
    independent_bytes      K independent copies (substrate duplicated K times)
    saving                 independent / bmx   (should GROW with K)
    marginal_bytes/agent   d(bmx_bytes)/dK     (should be ~flat = one layer)
    disagreements_ms       read-time compute over the whole matrix (should be ~linear)

No claim is made here beyond what the numbers show. Run:
    X:/miniconda3/python.exe X:/bitH/bhmemx/scale_test.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhmemx import Belief, MultiAgentReader, MultiAgentStore  # noqa: E402

F = 200                      # fixed substrate: 200 facts
KS = [3, 10, 25, 50, 100]   # agents
CONTEST = 0.30              # ~30% of facts contested
TMP = Path(__file__).resolve().parent / "_scale.bmx"


def _values(agent_idx: int, fact_idx: int) -> str:
    """Deterministic beliefs: contested facts split agents by parity."""
    if fact_idx % int(1 / CONTEST) == 0:           # contested
        return "true" if agent_idx % 2 == 0 else "false"
    return "true"                                   # uncontested -> consensus


def run() -> list[dict]:
    rows = []
    prev_bytes = None
    prev_k = None
    for k in KS:
        agents = [f"agent_{i:03d}" for i in range(k)]
        s = MultiAgentStore(agents)
        for j in range(F):
            s.add_fact(f"f{j}", f"description of fact {j}")
        for i, a in enumerate(agents):
            for j in range(F):
                s.believe(Belief(a, f"f{j}", _values(i, j), confidence=0.8))
        s.save(TMP)

        r = MultiAgentReader(TMP)
        sc = r.storage_comparison()

        t0 = time.perf_counter()
        dis = r.disagreements()
        r.agent_reliability()
        r.adjudicate("majority")
        r.adjudicate("weighted")
        compute_ms = (time.perf_counter() - t0) * 1000

        marginal = None
        if prev_bytes is not None:
            marginal = (sc["bmx_bytes"] - prev_bytes) / (k - prev_k)
        rows.append({
            "K": k,
            "bmx_bytes": sc["bmx_bytes"],
            "independent_bytes": sc["independent_copies_bytes"],
            "saving": sc["saving"],
            "marginal_bytes_per_agent": None if marginal is None else round(marginal),
            "n_disagreements": len(dis),
            "compute_ms": round(compute_ms, 1),
        })
        prev_bytes, prev_k = sc["bmx_bytes"], k
    TMP.unlink(missing_ok=True)
    return rows


def main() -> None:
    rows = run()
    print(f"\nbhmemx scaling — F={F} facts fixed, ~{int(CONTEST*100)}% contested\n")
    hdr = ("K", "bmx_KB", "indep_KB", "saving×", "marg_B/agent", "disagree", "compute_ms")
    print("  ".join(f"{h:>13}" for h in hdr))
    for r in rows:
        print("  ".join(f"{v:>13}" for v in (
            r["K"],
            round(r["bmx_bytes"] / 1024, 1),
            round(r["independent_bytes"] / 1024, 1),
            r["saving"],
            r["marginal_bytes_per_agent"] if r["marginal_bytes_per_agent"] is not None else "-",
            r["n_disagreements"],
            r["compute_ms"],
        )))
    first, last = rows[0], rows[-1]
    print(
        f"\nsaving grows {first['saving']}× (K={first['K']}) -> {last['saving']}× (K={last['K']});"
        f" marginal cost/agent ~flat at ~{rows[-1]['marginal_bytes_per_agent']} B;"
        f" read-time compute {first['compute_ms']}ms -> {last['compute_ms']}ms."
    )


if __name__ == "__main__":
    main()
