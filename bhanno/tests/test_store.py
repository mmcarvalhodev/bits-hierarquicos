"""bhanno tests — correctness as a gate before any claim of gain."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bhanno import AnnotationReader, AnnotationStore  # noqa: E402


def _store() -> AnnotationStore:
    s = AnnotationStore("ds", ["a", "b", "c"])
    # item0: unanimous (class 1); item1: contested (1,1,2); item2: split (1,2,3)
    for item in ("item0", "item1", "item2"):
        s.add_item(item, b"X" * 4000)  # heavy-ish shared substrate
    s.add_label("a", "item0", {"class": 1}); s.add_label("b", "item0", {"class": 1}); s.add_label("c", "item0", {"class": 1})
    s.add_label("a", "item1", {"class": 1}); s.add_label("b", "item1", {"class": 1}); s.add_label("c", "item1", {"class": 2})
    s.add_label("a", "item2", {"class": 1}); s.add_label("b", "item2", {"class": 2}); s.add_label("c", "item2", {"class": 3})
    return s


@pytest.fixture()
def an(tmp_path) -> AnnotationReader:
    p = tmp_path / "a.bha"
    _store().save(p)
    return AnnotationReader(p)


def test_item_returns_shared_substrate(an: AnnotationReader) -> None:
    data, stats = an.item("item0")
    assert data == b"X" * 4000
    assert stats.blocks_read == 1


def test_layer_returns_one_interpretation(an: AnnotationReader) -> None:
    labels, stats = an.layer("c")
    assert labels["item1"]["class"] == 2
    assert labels["item2"]["class"] == 3
    assert len(labels) == 3


def test_item_views_is_the_matrix(an: AnnotationReader) -> None:
    views, stats = an.item_views("item1")
    assert views == {"a": {"class": 1}, "b": {"class": 1}, "c": {"class": 2}}
    assert stats.blocks_read == 3


def test_disagreements_finds_contested_only(an: AnnotationReader) -> None:
    contested, stats = an.disagreements()
    ids = {c["id"] for c in contested}
    assert ids == {"item1", "item2"}          # item0 is unanimous, excluded
    item1 = next(c for c in contested if c["id"] == "item1")
    assert item1["majority"] == 1             # 2 of 3 voted class 1
    item2 = next(c for c in contested if c["id"] == "item2")
    assert item2["majority"] is None          # 1/1/1 split, no majority


def test_adjudicate_reports_agreement(an: AnnotationReader) -> None:
    adj, stats = an.adjudicate()
    assert adj["n_items"] == 3
    assert adj["unanimous"] == 1
    assert adj["contested"] == 2
    assert adj["majority"]["item0"] == 1


def test_adjudication_does_not_read_substrate(an: AnnotationReader) -> None:
    _, adj_stats = an.adjudicate()
    _, full_stats = an.full()
    # substrate is 3 * 100 bytes; adjudication must read far less than the whole
    assert adj_stats.bytes_read < full_stats.bytes_read


def test_storage_saving_shares_substrate(an: AnnotationReader) -> None:
    sc = an.storage_comparison()
    # independent copies duplicate the substrate K times → must be larger
    assert sc["independent_copies_bytes"] > sc["bha_bytes"]
    assert sc["saving"] > 1.0


def test_full_roundtrip(an: AnnotationReader) -> None:
    out, stats = an.full()
    assert set(out["items"]) == {"item0", "item1", "item2"}
    assert out["labels"]["b"]["item2"]["class"] == 2
    assert stats.bytes_read == an.file_size


def test_invalid_file_rejected(tmp_path) -> None:
    bad = tmp_path / "bad.bha"
    bad.write_bytes(b"NOPE" + b"\x00" * 20)
    with pytest.raises(ValueError):
        AnnotationReader(bad)
