"""F1 gate — roundtrip lossless bit-exact (spec §9)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import decode_full, encode  # noqa: E402

CASES = [
    ("flat_64", corpus.flat(64, 64)),
    ("flat_odd", corpus.flat(37, 23)),
    ("one_pixel", corpus.flat(1, 1, (255, 0, 7))),
    ("tiny_2x3", corpus.gradient(2, 3)),
    ("gradient_256", corpus.gradient(256, 256)),
    ("gradient_wide", corpus.gradient(317, 101)),
    ("shapes_512", corpus.shapes(512, 512)),
    ("noise_128x96", corpus.noise(128, 96)),
    ("hd_gradient", corpus.gradient(1920, 1080)),
]


@pytest.mark.parametrize("name,img", CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("pyramid", [True, False], ids=["pyr", "nopyr"])
def test_lossless_bit_exact(name, img, pyramid):
    blob, stats = encode(img, pyramid=pyramid)
    out, info = decode_full(blob)
    assert out.shape == img.shape
    assert np.array_equal(out, img), f"roundtrip não é bit-exact em {name}"
    assert info["bytes_read"] == len(blob)


def test_flat_compresses_noise_does_not():
    flat_blob, _ = encode(corpus.flat(256, 256), pyramid=False)
    noise_blob, _ = encode(corpus.noise(256, 256), pyramid=False)
    raw = 256 * 256 * 3
    assert len(flat_blob) < raw // 100, "imagem chapada deve colapsar a árvore"
    assert len(noise_blob) > raw, "ruído deve degenerar (custo > raw é esperado)"


def test_pyramid_overhead_is_bounded():
    img = corpus.noise(256, 256)
    with_pyr, _ = encode(img, pyramid=True)
    without, _ = encode(img, pyramid=False)
    overhead = (len(with_pyr) - len(without)) / len(without)
    # soma geométrica 1/4+1/16+... → ~33% sobre payload das folhas (spec §3.5)
    assert overhead < 0.40, f"overhead da pirâmide fora do previsto: {overhead:.2%}"


def test_lossy_threshold_zero_matches_lossless():
    img = corpus.shapes(128, 128)
    blob, _ = encode(img, lossy=True, threshold=0.0)
    out, _ = decode_full(blob)
    assert np.array_equal(out, img)


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        encode(np.zeros((10, 10), dtype=np.uint8))  # sem canal
    with pytest.raises(ValueError):
        encode(np.zeros((10, 10, 3), dtype=np.float32))  # dtype errado
    with pytest.raises(ValueError):
        decode_full(b"XXXX" + b"\x00" * 40)  # magic inválido
