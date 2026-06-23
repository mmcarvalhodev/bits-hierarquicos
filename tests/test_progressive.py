"""F2 gate — alegação C1: custo de leitura escala com a resolução pedida."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import decode_full, decode_progressive, encode  # noqa: E402


def test_full_level_equals_decode_full():
    img = corpus.shapes(256, 256)
    blob, stats = encode(img, pyramid=True)
    full, _ = decode_full(blob)
    prog, info = decode_progressive(blob, max_level=stats["levels"])
    assert np.array_equal(prog, full)
    assert info["bytes_read"] == len(blob)


def test_preview_is_valid_no_holes():
    # imagem sem preto: qualquer pixel (0,0,0) no preview = buraco não pintado
    img = corpus.gradient(256, 256)
    img = np.clip(img, 10, 255)
    blob, _ = encode(img, pyramid=True)
    for level in [0, 2, 4, 6]:
        prog, _ = decode_progressive(blob, max_level=level)
        assert prog.shape == img.shape
        assert (prog.reshape(-1, 3).sum(axis=1) > 0).all(), f"buraco no nível {level}"


def test_flat_preview_exact_at_any_level():
    img = corpus.flat(128, 128, (200, 10, 10))
    blob, _ = encode(img, pyramid=True)
    prog, info = decode_progressive(blob, max_level=0)
    assert np.array_equal(prog, img)  # raiz já é folha — preview perfeito
    assert info["bytes_read"] < 100


def test_bytes_read_monotonic_and_fraction_geometric():
    """O coração de C1: fração de bytes ≈ fração geométrica de pixels."""
    img = corpus.noise(512, 512)  # árvore densa — pior caso para C1
    blob, stats = encode(img, pyramid=True)
    n = stats["levels"]
    prev = 0
    for level in range(n + 1):
        _, info = decode_progressive(blob, max_level=level)
        # não-decrescente: com rampas, o último nível pode ser vazio
        # (blocos 2×2 viram RAMP no nível N-1 e o conteúdo termina lá)
        assert info["bytes_read"] >= prev, "bytes lidos não podem diminuir"
        prev = info["bytes_read"]
    # preview a 2 níveis do topo = 1/16 dos pixels; soma geométrica ≈ 8%
    _, info = decode_progressive(blob, max_level=n - 2)
    assert info["fraction"] < 0.15, f"fração C1 fora do geométrico: {info['fraction']:.2%}"
    _, info = decode_progressive(blob, max_level=n - 4)
    assert info["fraction"] < 0.02, f"thumbnail caro demais: {info['fraction']:.2%}"


def test_no_pyramid_partial_raises():
    blob, _ = encode(corpus.gradient(64, 64), pyramid=False)
    with pytest.raises(ValueError):
        decode_progressive(blob, max_level=2)


def test_no_pyramid_full_level_ok():
    img = corpus.gradient(64, 64)
    blob, stats = encode(img, pyramid=False)
    prog, _ = decode_progressive(blob, max_level=stats["levels"])
    assert np.array_equal(prog, img)
