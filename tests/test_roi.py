"""F2 gate — alegação C2: custo do ROI proporcional à área pedida."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import decode_full, decode_roi, encode  # noqa: E402

REGIONS = [
    (0, 0, 64, 64),        # canto
    (37, 51, 100, 80),     # offsets ímpares
    (200, 0, 56, 17),      # borda direita... depende da imagem
    (1, 1, 1, 1),          # 1 pixel
]


@pytest.mark.parametrize("maker", [corpus.shapes, corpus.gradient, corpus.noise],
                         ids=["shapes", "gradient", "noise"])
@pytest.mark.parametrize("region", REGIONS, ids=[str(r) for r in REGIONS])
def test_roi_bit_exact(maker, region):
    img = maker(256, 256)
    blob, _ = encode(img, pyramid=True)
    full, _ = decode_full(blob)
    x, y, w, h = region
    roi, info = decode_roi(blob, x, y, w, h)
    assert np.array_equal(roi, full[y : y + h, x : x + w])
    assert info["bytes_read"] <= len(blob)


def test_roi_full_image_equals_full_decode():
    img = corpus.shapes(200, 120)
    blob, _ = encode(img, pyramid=True)
    full, _ = decode_full(blob)
    roi, _ = decode_roi(blob, 0, 0, 200, 120)
    assert np.array_equal(roi, full)


def test_roi_payload_proportional_to_area():
    """O coração de C2: payload lido ∝ área, medido no pior caso (ruído)."""
    img = corpus.noise(512, 512)
    blob, _ = encode(img, pyramid=True)
    # 25% da área → ~23% do payload total: em ruído, blocos 2×2 viram RAMP
    # (12B) no nível N-1; ROI lê rampas mas não as médias da pirâmide.
    # Critério C2 da spec (≤1.2× área) continua respeitado.
    _, info = decode_roi(blob, 0, 0, 256, 256)
    assert 0.18 < info["payload_fraction"] < 0.28, info["payload_fraction"]
    # ~1% da área → payload ~1%
    _, info = decode_roi(blob, 100, 100, 51, 51)
    assert info["payload_fraction"] < 0.02, info["payload_fraction"]


def test_roi_out_of_bounds_raises():
    blob, _ = encode(corpus.flat(64, 64))
    for bad in [(-1, 0, 10, 10), (0, 0, 65, 10), (60, 60, 10, 10), (0, 0, 0, 5)]:
        with pytest.raises(ValueError):
            decode_roi(blob, *bad)


def test_roi_instrumentation_fields():
    blob, _ = encode(corpus.shapes(128, 128))
    _, info = decode_roi(blob, 10, 10, 30, 30)
    for field in ["bytes_read", "struct_bytes_read", "payload_bytes_read",
                  "total_payload_bytes", "fraction", "payload_fraction",
                  "seeks", "roi_area_fraction"]:
        assert field in info
    assert info["bytes_read"] == info["struct_bytes_read"] + info["payload_bytes_read"]
