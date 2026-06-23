"""F3 gate — curva tamanho×PSNR monotónica (spec §9)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import decode_full, encode  # noqa: E402
from bhc.metrics import psnr  # noqa: E402

THRESHOLDS = [0.0, 4.0, 16.0, 64.0]


def _curve(img):
    points = []
    for t in THRESHOLDS:
        blob, _ = encode(img, lossy=True, threshold=t, pyramid=False)
        out, _ = decode_full(blob)
        points.append((t, len(blob), psnr(img, out)))
    return points


@pytest.mark.parametrize("maker", [corpus.gradient, corpus.natural_proxy],
                         ids=["gradient", "natural_proxy"])
def test_size_psnr_curve_monotonic(maker):
    img = maker(512, 512)
    points = _curve(img)
    sizes = [p[1] for p in points]
    psnrs = [p[2] for p in points]
    assert all(a >= b for a, b in zip(sizes, sizes[1:])), f"tamanho não-monotónico: {sizes}"
    assert all(a >= b for a, b in zip(psnrs, psnrs[1:])), f"PSNR não-monotónico: {psnrs}"
    assert sizes[0] > sizes[-1], "threshold maior deve comprimir mais"


def test_lossless_is_psnr_inf():
    img = corpus.shapes(128, 128)
    blob, _ = encode(img)
    out, _ = decode_full(blob)
    assert psnr(img, out) == float("inf")


def test_lossy_error_bounded_by_threshold():
    """Erro máximo por pixel ≤ threshold: a folha pinta a média de um
    quadrante cujo spread por canal é ≤ threshold."""
    img = corpus.natural_proxy(256, 256)
    t = 16.0
    blob, _ = encode(img, lossy=True, threshold=t, pyramid=False)
    out, _ = decode_full(blob)
    max_err = int(np.abs(img.astype(int) - out.astype(int)).max())
    assert max_err <= t, f"erro máximo {max_err} excede threshold {t}"


def test_psnr_rejects_shape_mismatch():
    with pytest.raises(ValueError):
        psnr(np.zeros((4, 4, 3), np.uint8), np.zeros((4, 5, 3), np.uint8))
