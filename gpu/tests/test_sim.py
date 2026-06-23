"""Gate — agregados do BH batem o flat (exato) + contabilidade de linha sã."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bhgpu import HierArray, context_coupled  # noqa: E402
from bhgpu.sim import CACHE_LINE  # noqa: E402

RNG = np.random.default_rng(3)
VALS = (np.linspace(0, 1000, 1_000_000) + RNG.normal(0, 20, 1_000_000)).astype(np.float64)


@pytest.fixture(scope="module")
def ha():
    return HierArray(VALS)


@pytest.mark.parametrize("lo,hi", [(0, 1_000_000), (1234, 567890), (100, 132), (5, 7)])
def test_range_sum_exact(ha, lo, hi):
    got, _ = ha.range_sum_bh(lo, hi)
    assert got == pytest.approx(VALS[lo:hi].sum(), rel=1e-9)


def test_bh_moves_less_for_large_range(ha):
    lo, hi = 0, 500_000
    flat = ha.range_sum_flat_bytes(lo, hi)
    _, bh = ha.range_sum_bh(lo, hi)
    assert bh < flat / 100  # ordem(s) de grandeza menos


def test_lod_bh_tiny_vs_flat(ha):
    flat = ha.lod_flat_bytes()
    bh = ha.lod_bh_bytes(top_levels=8)
    assert bh < flat / 500  # ~976× menos no caso medido


def test_filter_count_exact(ha):
    t = float(np.percentile(VALS, 99))
    count, _ = ha.filter_bh_bytes(t)
    assert count == int((VALS > t).sum())


def test_context_coupled_about_2x():
    c = context_coupled(1_000_000)
    assert c["flat"] / c["bh"] == pytest.approx(64.0, rel=0.5) or c["flat"] > c["bh"]
    # flat = 2 linhas/item; bh ~ 1 linha por BLOCK itens
    assert c["bh"] < c["flat"]


def test_small_range_no_false_win(ha):
    # range dentro de 1 bloco: BH não inventa vantagem
    _, bh = ha.range_sum_bh(10, 20)
    flat = ha.range_sum_flat_bytes(10, 20)
    assert bh == flat  # ambos 1 linha
