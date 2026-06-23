"""Métricas de qualidade e contadores (spec §7)."""
from __future__ import annotations

import numpy as np


def psnr(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """PSNR em dB entre duas imagens uint8. inf = idênticas."""
    if original.shape != reconstructed.shape:
        raise ValueError("dimensões diferentes")
    mse = np.mean(
        (original.astype(np.float64) - reconstructed.astype(np.float64)) ** 2
    )
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10((255.0**2) / mse))
