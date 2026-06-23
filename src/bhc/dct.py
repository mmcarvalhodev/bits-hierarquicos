"""Mini-DCT interpretation for BHC v0.3.

This is intentionally small: each DCT node stores the 4x4 low-frequency
coefficients for each RGB channel as int16. The node size is known from the
hierarchy level, so no per-node dimensions are stored.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

COEFF_N = 4
PAYLOAD_BYTES = COEFF_N * COEFF_N * 3 * 2


@lru_cache(maxsize=None)
def _basis(n: int) -> np.ndarray:
    x = np.arange(n, dtype=np.float64)
    u = np.arange(n, dtype=np.float64)[:, None]
    b = np.cos(np.pi * (2.0 * x + 1.0) * u / (2.0 * n))
    b[0] *= np.sqrt(1.0 / n)
    b[1:] *= np.sqrt(2.0 / n)
    return b


def encode_blocks(blocks: np.ndarray) -> np.ndarray:
    """Encode blocks (n, s, s, 3) to (n, 4, 4, 3) int16 coefficients."""
    if blocks.ndim != 4 or blocks.shape[-1] != 3:
        raise ValueError("expected blocks shaped (n, s, s, 3)")
    s = blocks.shape[1]
    if blocks.shape[2] != s or s < COEFF_N:
        raise ValueError("DCT blocks must be square and at least 4x4")
    b = _basis(s)[:COEFF_N]
    centered = blocks.astype(np.float64) - 128.0
    coeff = np.einsum("uy,nxyc,vx->nuvc", b, centered, b, optimize=True)
    return np.clip(np.rint(coeff), -32768, 32767).astype(np.int16)


def reconstruct(coeff: np.ndarray, s: int) -> np.ndarray:
    """Reconstruct (n, 4, 4, 3) int16 coefficients to (n, s, s, 3)."""
    if coeff.ndim != 4 or coeff.shape[1:3] != (COEFF_N, COEFF_N):
        raise ValueError("expected DCT coeffs shaped (n, 4, 4, 3)")
    b = _basis(s)[:COEFF_N]
    rec = np.einsum("uy,nuvc,vx->nxyc", b, coeff.astype(np.float64), b, optimize=True)
    return np.clip(np.rint(rec + 128.0), 0, 255).astype(np.uint8)
