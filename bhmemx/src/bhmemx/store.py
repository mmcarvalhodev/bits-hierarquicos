"""bhmemx — multi-agent memory that exercises FCIR property 3-4 (preserved
disagreement), not 1-2 (selective read).

The meta-critique was right that the prototypes so far measured selective read
(property 1-2, already SOTA). This one exercises the differentiator: multiple
agents hold beliefs about a SHARED fact substrate; their beliefs may CONTRADICT;
the contradiction is **preserved and queryable**, and adjudication is deferred,
optional and non-destructive.

The readings here are about COMPUTING OVER DISAGREEMENT, not bytes:

    fact_views(fact)       all agents' beliefs about one fact (the matrix)
    disagreements()        facts where agents contradict — preserved, not resolved
    agent_reliability()    which agent most often dissents from the majority
    adjudicate(rule)       majority / confidence-weighted consensus — at READ time,
                           never written back; the rival beliefs stay

Honest baseline (stated, not hidden): every query below is also answerable by an
uncollapsed (fact, agent, value) table — it is a GROUP BY. FCIR's delta over that
table is co-registration to the shared substrate stored once, and a single model.
What FCIR is NOT is a new *capability* vs an uncollapsed table; it IS a discipline
+ model for 'do not collapse on write'. (See ../directions/RESULTS_DISAGREEMENT_COMPUTE.md.)
The genuine win vs current multi-agent systems is that those force consensus and
discard the dissent; bhmemx keeps it first-class.
"""
from __future__ import annotations

import json
import os
import struct
from collections import Counter
from dataclasses import dataclass

MAGIC = b"BMX1"
_U32 = struct.Struct("<I")


@dataclass
class Belief:
    """One agent's belief about one fact."""

    agent: str
    fact: str
    value: str
    confidence: float = 1.0
    ts: int = 0


class MultiAgentStore:
    """Shared fact substrate + per-agent belief layers, serialized as .bmx.

        MAGIC(4)
        header_len(4) + header_json   {agents:[...], n_facts}
        facts_len(4)  + facts_json    [{id, desc}]                 (substrate, once)
        layers_len(4) + layers_json   {agent: {fact: [value, conf, ts]}}
    """

    def __init__(self, agents: list[str]) -> None:
        self.agents = list(agents)
        self._facts: dict[str, str] = {}          # fact_id -> description
        self._layers: dict[str, dict] = {a: {} for a in agents}

    def add_fact(self, fact_id: str, desc: str) -> None:
        self._facts[fact_id] = desc

    def believe(self, b: Belief) -> None:
        self._layers[b.agent][b.fact] = [b.value, b.confidence, b.ts]

    def save(self, path: str | os.PathLike) -> str:
        header = json.dumps({"agents": self.agents, "n_facts": len(self._facts)}).encode()
        facts = json.dumps([{"id": k, "desc": v} for k, v in self._facts.items()]).encode()
        layers = json.dumps(self._layers, ensure_ascii=False).encode()
        with open(path, "wb") as f:
            f.write(MAGIC)
            for blob in (header, facts, layers):
                f.write(_U32.pack(len(blob)))
                f.write(blob)
        return str(path)


class MultiAgentReader:
    def __init__(self, path: str | os.PathLike) -> None:
        self.path = str(path)
        self.file_size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            if f.read(4) != MAGIC:
                raise ValueError("not a .bmx file (bhmemx)")
            self.header = json.loads(self._blob(f))
            self.facts = {e["id"]: e["desc"] for e in json.loads(self._blob(f))}
            self.layers = json.loads(self._blob(f))
        self.agents = self.header["agents"]

    @staticmethod
    def _blob(f) -> bytes:
        (n,) = _U32.unpack(f.read(4))
        return f.read(n)

    # ---- the matrix: all agents' beliefs about one fact ----
    def fact_views(self, fact: str) -> dict:
        return {a: self.layers[a][fact][0] for a in self.agents if fact in self.layers[a]}

    def belief(self, agent: str, fact: str):
        e = self.layers.get(agent, {}).get(fact)
        return e[0] if e else None

    # ---- where agents contradict — preserved, not resolved ----
    def disagreements(self) -> list[dict]:
        out = []
        for fact in self.facts:
            views = self.fact_views(fact)
            if len(set(views.values())) > 1:
                tally = Counter(views.values())
                top, n = tally.most_common(1)[0]
                out.append({"fact": fact, "views": views,
                            "majority": top if n * 2 > len(views) else None,
                            "agreement": round(n / len(views), 2)})
        return out

    # ---- which agent most often dissents from the majority ----
    def agent_reliability(self) -> list[tuple]:
        dissent = Counter({a: 0 for a in self.agents})
        for fact in self.facts:
            views = self.fact_views(fact)
            if not views:
                continue
            maj = Counter(views.values()).most_common(1)[0][0]
            for a, v in views.items():
                if v != maj:
                    dissent[a] += 1
        return dissent.most_common()

    # ---- optional, read-time, non-destructive adjudication ----
    def adjudicate(self, rule: str = "majority") -> dict:
        out = {}
        for fact in self.facts:
            views = {a: self.layers[a][fact] for a in self.agents if fact in self.layers[a]}
            if not views:
                continue
            if rule == "weighted":
                w = Counter()
                for a, (v, conf, _) in views.items():
                    w[v] += conf
                out[fact] = w.most_common(1)[0][0]
            else:  # majority
                tally = Counter(v for v, _, _ in views.values())
                top, n = tally.most_common(1)[0]
                out[fact] = top if n * 2 > len(views) else None  # None = undecided
        return out

    # ---- storage: substrate once + K layers vs K agent copies ----
    def storage_comparison(self) -> dict:
        substrate = sum(len(json.dumps({"id": k, "desc": v})) for k, v in self.facts.items())
        labels = sum(len(json.dumps(self.layers[a])) for a in self.agents)
        k = len(self.agents)
        independent = k * substrate + labels
        return {"substrate_bytes": substrate, "label_bytes": labels, "agents": k,
                "bmx_bytes": self.file_size, "independent_copies_bytes": independent,
                "saving": round(independent / self.file_size, 2) if self.file_size else 0}
