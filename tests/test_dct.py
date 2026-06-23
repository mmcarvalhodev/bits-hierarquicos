"""v0.3 -- frequency interpretation: DCT terminal nodes."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import decode_full, decode_progressive, decode_roi, encode  # noqa: E402
from bhc.metrics import psnr  # noqa: E402


def test_natural_proxy_uses_dct_nodes():
    img = corpus.natural_proxy(512, 512)
    blob, stats = encode(img, lossy=True, threshold=24.0, pyramid=False)
    out, _ = decode_full(blob)
    assert stats["total_dct"] > 0
    assert psnr(img, out) > 32.0
    assert len(blob) < img.nbytes // 2


def test_dct_roi_matches_full_decode():
    img = corpus.natural_proxy(256, 256)
    blob, stats = encode(img, lossy=True, threshold=24.0, pyramid=True)
    assert stats["total_dct"] > 0
    full, _ = decode_full(blob)
    roi, _ = decode_roi(blob, 41, 57, 133, 91)
    assert np.array_equal(roi, full[57:148, 41:174])


def test_dct_full_progressive_matches_full_decode():
    img = corpus.natural_proxy(256, 256)
    blob, stats = encode(img, lossy=True, threshold=24.0, pyramid=False)
    full, _ = decode_full(blob)
    prog, _ = decode_progressive(blob, max_level=stats["levels"])
    assert np.array_equal(prog, full)
