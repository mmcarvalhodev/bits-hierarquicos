"""Gate — reconstrução exata por camada + estrutura partilhada (W1) / fronteira (W3)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bhwafer import (
    measure, measure_with_derived, measure_with_refinements, reconstruct_layer,
    reconstruct_with_refinements,
)  # noqa: E402


def make_partition(side, seed, p=0.7, minb=4):
    rng = np.random.default_rng(seed)
    region = np.zeros((side, side), dtype=np.int32)
    nid = [0]

    def rec(y, x, s):
        if s <= minb or rng.random() > p:
            region[y:y + s, x:x + s] = nid[0]; nid[0] += 1; return
        h = s // 2
        for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
            rec(y + dy, x + dx, h)
    rec(0, 0, side)
    return region


def layer_from(region, channels, seed):
    rng = np.random.default_rng(seed)
    vals = rng.integers(0, 256, (region.max() + 1, channels), dtype=np.uint8)
    return vals[region]


def test_lossless_reconstruction_each_layer():
    reg = make_partition(128, seed=1)
    layers = [layer_from(reg, 3, 10), layer_from(reg, 1, 11), layer_from(reg, 3, 12)]
    for li, L in enumerate(layers):
        rec = reconstruct_layer(layers, li, threshold=0.0)
        assert np.array_equal(rec, L), f"camada {li} não reconstruiu exata"


def test_w1_coregistered_shares_structure():
    """Camadas que partilham a partição → wafer grava estrutura 1×.

    A alegação é sobre ESTRUTURA (amortizada ~K×), não sobre o total — que
    pode ser ganho pequeno quando o payload domina (achado honesto do MVP)."""
    reg = make_partition(256, seed=2)
    layers = [layer_from(reg, 3, s) for s in (20, 21, 22)]
    m = measure(layers, threshold=0.0)
    # estrutura independente ≈ K × estrutura do wafer (mesma partição)
    assert m["indep"]["struct"] > 2.5 * m["wafer"]["struct"]
    assert m["struct_saved"] > 0
    assert m["ratio"] > 1.0  # wafer é menor — magnitude depende da fração-estrutura


def test_w2_payload_not_magically_shared():
    """O payload do wafer ≈ soma dos independentes (Shannon: sem mágica)."""
    reg = make_partition(256, seed=3)
    layers = [layer_from(reg, 3, s) for s in (30, 31, 32)]
    m = measure(layers, threshold=0.0)
    # mesma partição → mesmas folhas → payload do wafer == soma (overhead 0)
    assert m["payload_overhead"] == 0
    assert m["wafer"]["payload"] == m["indep"]["payload"]


def test_derived_layer_reduces_payload_honestly():
    reg = make_partition(256, seed=7)
    base = layer_from(reg, 3, 70)
    derived = base[:, :, :1]  # deterministic toy derivation from base
    other = layer_from(reg, 3, 71)
    raw = measure([base, derived, other], threshold=0.0)
    pred = measure_with_derived([base, derived, other], derived={1}, threshold=0.0)
    assert pred["wafer"]["struct"] == raw["wafer"]["struct"]
    assert pred["wafer"]["payload"] < raw["wafer"]["payload"]
    assert pred["derived_payload_saved"] == raw["wafer"]["leaves"] * 1


def test_refinements_do_not_drag_base_tree():
    base = np.zeros((256, 256, 3), dtype=np.uint8)
    yy, xx = np.indices((256, 256))
    detail = (((xx + yy) & 1) * 255).astype(np.uint8)[:, :, None]
    union = measure([base, detail], threshold=0.0)
    refined = measure_with_refinements([base, detail], base_layer=0, threshold=0.0)
    assert refined["wafer"]["base_leaves"] < union["wafer"]["leaves"]
    assert refined["wafer"]["total"] < union["wafer"]["total"]


def test_refinements_reconstruct_exact_with_derived_rule():
    reg = make_partition(128, seed=10)
    rgb = layer_from(reg, 3, 90)
    lum = np.rint(rgb @ [0.299, 0.587, 0.114]).astype(np.uint8)[:, :, None]
    seg = ((rgb >> 5) << 5)
    layers = [rgb, lum, seg]
    refined = measure_with_refinements(layers, base_layer=0, derived={1}, threshold=24.0)
    recon = reconstruct_with_refinements(
        layers,
        base_layer=0,
        derived_rules={1: lambda base: np.rint(base @ [0.299, 0.587, 0.114]).astype(np.uint8)[:, :, None]},
        threshold=24.0,
    )
    assert refined["ratio"] > 1.0
    for got, exp in zip(recon, layers):
        assert np.array_equal(got, exp)


def test_w3_misaligned_loses():
    """Camadas desalinhadas → união super-subdivide → wafer pior."""
    layers = [layer_from(make_partition(256, seed=s), 3, s + 100) for s in (4, 5, 6)]
    m = measure(layers, threshold=0.0)
    assert m["ratio"] < 1.0, m["ratio"]  # wafer perde, como esperado
    assert m["payload_overhead"] > 0     # união tem mais folhas
