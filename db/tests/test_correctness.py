"""Gate de correção — BH bate a tabela plana EXATAMENTE antes de medir."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bhdb import AggregateTree, make_dataset  # noqa: E402
from bhdb import table as T  # noqa: E402

TBL = make_dataset(50_000, seed=11)


@pytest.fixture(scope="module")
def tree():
    return AggregateTree(TBL, col="val_trend", block=256)


def test_global_sum_exact(tree):
    res, _ = tree.aggregate_global()
    assert res["sum"] == pytest.approx(float(TBL.val_trend.sum()), rel=1e-9)
    assert res["count"] == len(TBL)
    assert res["min"] == pytest.approx(float(TBL.val_trend.min()))
    assert res["max"] == pytest.approx(float(TBL.val_trend.max()))


@pytest.mark.parametrize("frac", [0.001, 0.05, 0.5, 0.99])
def test_range_sum_exact(tree, frac):
    span = TBL.key[-1] - TBL.key[0]
    lo = int(TBL.key[0] + span * 0.2)
    hi = int(lo + span * frac)
    res, _ = tree.aggregate_range(lo, hi)
    exp_sum, _ = T.range_scan_sum(TBL.key, TBL.val_trend, lo, hi)
    _, info = T.range_scan_sum(TBL.key, TBL.val_trend, lo, hi)
    assert res["sum"] == pytest.approx(exp_sum, rel=1e-9)
    assert res["count"] == info["rows_read"]


def test_range_edge_cases(tree):
    # range vazio
    res, _ = tree.aggregate_range(TBL.key[-1] + 1000, TBL.key[-1] + 2000)
    assert res["count"] == 0
    # range inteiro
    res, _ = tree.aggregate_range(int(TBL.key[0]) - 1, int(TBL.key[-1]) + 1)
    assert res["count"] == len(TBL)
    assert res["sum"] == pytest.approx(float(TBL.val_trend.sum()), rel=1e-9)
    # range dentro de um único bloco
    lo = int(TBL.key[10]); hi = int(TBL.key[20])
    res, _ = tree.aggregate_range(lo, hi)
    exp, _ = T.range_scan_sum(TBL.key, TBL.val_trend, lo, hi)
    assert res["sum"] == pytest.approx(exp, rel=1e-9)


@pytest.mark.parametrize("op,pct", [("gt", 99), ("gt", 50), ("lt", 1), ("lt", 50)])
def test_prune_filter_count_exact(tree, op, pct):
    t = float(np.percentile(TBL.val_trend, pct))
    count, _ = tree.prune_filter_count(op, t)
    expected, _ = T.filter_scan_count(TBL.val_trend, op, t)
    assert count == expected


def test_prune_range_count_exact(tree):
    span = TBL.key[-1] - TBL.key[0]
    lo = int(TBL.key[0] + span * 0.3)
    hi = int(lo + span * 0.1)
    count, _ = tree.prune_range_count(lo, hi)
    expected = int(((TBL.key >= lo) & (TBL.key <= hi)).sum())
    assert count == expected


def test_raw_scan_matches_full(tree):
    total, info = tree.raw_scan_sum()
    assert total == pytest.approx(float(TBL.val_trend.sum()), rel=1e-9)
    assert info["rows_read"] == len(TBL)


def test_off_axis_region_exact(tree):
    count, info = tree.off_axis_region_count(3)
    expected, _ = T.filter_scan_eq_count(TBL.region, 3)
    assert count == expected
    assert info["rows_read"] == len(TBL)  # D3: sem poda, lê tudo


def test_region_count_exact(tree):
    count, info = tree.region_count(3)
    expected, _ = T.filter_scan_eq_count(TBL.region, 3)
    assert count == expected
    assert info["rows_read"] == 0


def test_region_count_range_exact(tree):
    span = TBL.key[-1] - TBL.key[0]
    lo = int(TBL.key[0] + span * 0.25)
    hi = int(lo + span * 0.4)
    count, _ = tree.region_count_range(3, lo, hi)
    mask = (TBL.key >= lo) & (TBL.key <= hi) & (TBL.region == 3)
    assert count == int(mask.sum())


def test_val_rand_tree_also_exact():
    tr = AggregateTree(TBL, col="val_rand", block=256)
    t = float(np.percentile(TBL.val_rand, 99))
    count, _ = tr.prune_filter_count("gt", t)
    expected, _ = T.filter_scan_count(TBL.val_rand, "gt", t)
    assert count == expected


def test_same_tree_prunes_val_rand_exact(tree):
    t = float(np.percentile(TBL.val_rand, 99))
    count, _ = tree.prune_filter_count_col("val_rand", "gt", t)
    expected, _ = T.filter_scan_count(TBL.val_rand, "gt", t)
    assert count == expected
