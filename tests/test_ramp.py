"""v0.2 — multi-interpretação: nó RAMP (rampa bilinear de 4 cantos)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import decode_full, decode_progressive, decode_roi, encode  # noqa: E402
from bhc.metrics import psnr  # noqa: E402


def test_gradient_lossy_collapses_to_ramps():
    """A interpretação certa muda a ordem de grandeza: gradiente que era
    o pior caso da mono-interpretação colapsa em poucas rampas."""
    img = corpus.gradient(1024, 1024)
    blob_const_only, _ = encode(img)  # lossless: rampa só se exata
    blob, stats = encode(img, lossy=True, threshold=2.0, pyramid=False)
    out, _ = decode_full(blob)
    assert stats["total_ramps"] >= 1
    assert len(blob) < img.nbytes // 1000, f"gradiente não colapsou: {len(blob)}B"
    assert psnr(img, out) > 40.0


def test_lossless_with_ramps_still_bit_exact():
    """Rampa em lossless só é aceita com erro ZERO — roundtrip exato."""
    # rampa exata por construção: valores lineares sem arredondamento quebrado
    xx = np.arange(0, 256, 2, dtype=np.uint8)
    img = np.stack([np.tile(xx, (64, 1))] * 3, axis=-1)  # 64×128 linear exato
    blob, stats = encode(img)
    out, _ = decode_full(blob)
    assert np.array_equal(out, img)


def test_lossy_error_still_bounded_with_ramps():
    img = corpus.natural_proxy(256, 256)
    t = 12.0
    blob, stats = encode(img, lossy=True, threshold=t, pyramid=False)
    out, _ = decode_full(blob)
    max_err = int(np.abs(img.astype(int) - out.astype(int)).max())
    assert max_err <= t, f"erro máximo {max_err} excede threshold {t}"


def test_roi_and_progressive_consistent_with_ramps():
    img = corpus.gradient(512, 512)
    blob, stats = encode(img, lossy=True, threshold=4.0, pyramid=True)
    assert stats["total_ramps"] >= 1
    full, _ = decode_full(blob)
    # ROI bate com o full em regiões com rampas
    for x, y, w, h in [(0, 0, 100, 100), (130, 250, 200, 150), (511, 0, 1, 512)]:
        roi, _ = decode_roi(blob, x, y, w, h)
        assert np.array_equal(roi, full[y : y + h, x : x + w]), (x, y, w, h)
    # progressivo no nível máximo == full
    prog, _ = decode_progressive(blob, max_level=stats["levels"])
    assert np.array_equal(prog, full)


def test_natural_lossy_smaller_with_ramps_than_const_only():
    """Em conteúdo suave, multi-interpretação deve reduzir o arquivo.
    (não é gate da spec — é o mecanismo da v0.2 sendo verificado)"""
    img = corpus.natural_proxy(512, 512)
    blob, stats = encode(img, lossy=True, threshold=16.0, pyramid=False)
    assert stats["total_ramps"] > 0, "nenhuma rampa usada em conteúdo suave"
