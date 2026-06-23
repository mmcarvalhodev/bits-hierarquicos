"""Interpretação RAMP — rampa bilinear a partir de 4 cantos (v0.2).

Encoder e decoder usam EXATAMENTE a mesma reconstrução (incluindo
arredondamento), garantindo que o erro aceito no encode é o erro
observado no decode.
"""
from __future__ import annotations

import numpy as np


def weights(s: int) -> np.ndarray:
    """Pesos bilineares (4, s, s) float32 na ordem TL, TR, BL, BR."""
    if s < 2:
        raise ValueError("rampa requer quadrante >= 2x2")
    r = (np.arange(s, dtype=np.float32)) / (s - 1)
    wy0, wy1 = 1.0 - r, r          # topo / fundo
    wx0, wx1 = 1.0 - r, r          # esquerda / direita
    return np.stack([
        np.outer(wy0, wx0),  # TL
        np.outer(wy0, wx1),  # TR
        np.outer(wy1, wx0),  # BL
        np.outer(wy1, wx1),  # BR
    ]).astype(np.float32)


def reconstruct(corner_vals: np.ndarray, s: int) -> np.ndarray:
    """(n, 4, 3) uint8 → (n, s, s, 3) uint8 via interpolação bilinear."""
    w = weights(s)
    pred = np.einsum("ncv,cyx->nyxv", corner_vals.astype(np.float32), w)
    return np.clip(np.rint(pred), 0, 255).astype(np.uint8)
