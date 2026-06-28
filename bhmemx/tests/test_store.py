"""bhmemx tests — correctness as a gate; focus on the property-3-4 reads."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bhmemx import Belief, MultiAgentReader, MultiAgentStore  # noqa: E402


def _store() -> MultiAgentStore:
    s = MultiAgentStore(["a", "b", "c"])
    for fact in ("f0", "f1", "f2"):
        s.add_fact(fact, f"desc {fact}")
    # f0 unanimous (true); f1 majority (true,true,false); f2 split (true,false,unknown)
    for a, v in [("a", "true"), ("b", "true"), ("c", "true")]:
        s.believe(Belief(a, "f0", v))
    for a, v in [("a", "true"), ("b", "true"), ("c", "false")]:
        s.believe(Belief(a, "f1", v, confidence=0.9 if a != "c" else 0.95))
    for a, v in [("a", "true"), ("b", "false"), ("c", "unknown")]:
        s.believe(Belief(a, "f2", v))
    return s


@pytest.fixture()
def r(tmp_path) -> MultiAgentReader:
    p = tmp_path / "m.bmx"
    _store().save(p)
    return MultiAgentReader(p)


def test_fact_views_is_the_matrix(r):
    assert r.fact_views("f1") == {"a": "true", "b": "true", "c": "false"}


def test_disagreements_preserved(r):
    dis = {d["fact"] for d in r.disagreements()}
    assert dis == {"f1", "f2"}                 # f0 unanimous, excluded
    f1 = next(d for d in r.disagreements() if d["fact"] == "f1")
    assert f1["majority"] == "true"
    f2 = next(d for d in r.disagreements() if d["fact"] == "f2")
    assert f2["majority"] is None              # 3-way split, no majority


def test_agent_reliability(r):
    rel = dict(r.agent_reliability())
    assert rel["c"] >= 2                        # c dissents on f1 and f2
    assert rel["a"] == 0                        # a is always with the majority


def test_adjudicate_majority_and_weighted(r):
    maj = r.adjudicate("majority")
    assert maj["f0"] == "true" and maj["f1"] == "true" and maj["f2"] is None
    wgt = r.adjudicate("weighted")
    assert wgt["f1"] == "true"                  # confidence-weighted still 'true' here


def test_adjudication_is_non_destructive(r):
    before = r.fact_views("f1")
    r.adjudicate("majority")
    r.adjudicate("weighted")
    assert r.fact_views("f1") == before         # rival beliefs untouched


def test_storage_shares_substrate(r):
    sc = r.storage_comparison()
    assert sc["independent_copies_bytes"] > sc["bmx_bytes"]
    assert sc["saving"] > 1.0


def test_invalid_file(tmp_path):
    bad = tmp_path / "bad.bmx"
    bad.write_bytes(b"NOPE" + b"\x00" * 16)
    with pytest.raises(ValueError):
        MultiAgentReader(bad)
