"""Gate de leitura — D1/D2 lêem fração; D3 não poda (a fronteira)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bhdb import AggregateTree, make_dataset  # noqa: E402

TBL = make_dataset(200_000, seed=5)
BLOCK = 1024


@pytest.fixture(scope="module")
def tree():
    return AggregateTree(TBL, col="val_trend", block=BLOCK)


def test_d1_global_reads_no_rows(tree):
    _, info = tree.aggregate_global()
    assert info["rows_read"] == 0  # só a raiz


def test_d1_range_reads_at_most_two_blocks(tree):
    """Agregado de range grande lê só os 2 blocos de fronteira (≪ range)."""
    span = TBL.key[-1] - TBL.key[0]
    lo = int(TBL.key[0] + span * 0.1)
    hi = int(lo + span * 0.6)  # range enorme (60%)
    _, info = tree.aggregate_range(lo, hi)
    assert info["rows_read"] <= 2 * BLOCK, info
    # ganho gigante: 60% de 200k = ~120k linhas no plano vs ~2k no BH
    assert info["rows_read"] < 0.05 * len(TBL)


def test_d2_key_range_prunes(tree):
    """Filtro no eixo organizado (key): lê ∝ seletividade + fronteira."""
    span = TBL.key[-1] - TBL.key[0]
    lo = int(TBL.key[0] + span * 0.4)
    hi = int(lo + span * 0.02)  # 2% seletivo
    _, info = tree.prune_range_count(lo, hi)
    assert info["rows_read"] < 0.06 * len(TBL), info  # ~2% + fronteira


def test_d2_correlated_value_prunes(tree):
    """val_trend correlaciona com key → poda por min/max funciona."""
    t = float(np.percentile(TBL.val_trend, 99))  # 1% seletivo
    _, info = tree.prune_filter_count("gt", t)
    # poda forte: lê muito menos que a tabela inteira
    assert info["rows_read"] < 0.25 * len(TBL), info


def test_d3_independent_value_prunes_poorly(tree):
    """val_rand independente da key → poda fraca (a fronteira do paradigma)."""
    t = float(np.percentile(TBL.val_rand, 99))  # 1% seletivo, mas espalhado
    _, info = tree.prune_filter_count_col("val_rand", "gt", t)
    # quase todo bloco tem algum valor alto → poda quase nula
    assert info["rows_read"] > 0.8 * len(TBL), info


def test_d3_off_axis_region_no_pruning(tree):
    """Filtro por região (não agregada): lê tudo. Perda declarada."""
    _, info = tree.off_axis_region_count(2)
    assert info["rows_read"] == len(TBL)


def test_region_interpretation_reads_no_rows(tree):
    """Com contador por regiao materializado, o mesmo predicado vira agregado."""
    _, info = tree.region_count(2)
    assert info["rows_read"] == 0
    assert info["nodes_read"] == 1


def test_region_range_reads_only_boundaries(tree):
    span = TBL.key[-1] - TBL.key[0]
    lo = int(TBL.key[0] + span * 0.2)
    hi = int(lo + span * 0.5)
    _, info = tree.region_count_range(2, lo, hi)
    assert info["rows_read"] <= 2 * BLOCK, info


def test_d3_low_selectivity_no_benefit(tree):
    """Filtro que casa ~metade: poda inútil mesmo no eixo certo."""
    t = float(np.percentile(TBL.val_trend, 50))
    _, info = tree.prune_filter_count("gt", t)
    assert info["rows_read"] > 0.4 * len(TBL), info
