"""Geradores do corpus sintético (spec §6) + carga de imagens reais."""
from __future__ import annotations

import numpy as np


def flat(w: int, h: int, color: tuple[int, int, int] = (40, 90, 200)) -> np.ndarray:
    img = np.empty((h, w, 3), dtype=np.uint8)
    img[:] = color
    return img


def gradient(w: int, h: int) -> np.ndarray:
    """Gradiente horizontal+vertical — quase nenhum quadrante homogéneo."""
    x = np.linspace(0, 255, w, dtype=np.float64)
    y = np.linspace(0, 255, h, dtype=np.float64)
    xx, yy = np.meshgrid(x, y)
    img = np.stack([xx, yy, (xx + yy) / 2], axis=-1)
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def shapes(w: int, h: int, seed: int = 7, n: int = 40) -> np.ndarray:
    """Retângulos chapados sobre fundo liso — caso forte da quadtree."""
    rng = np.random.default_rng(seed)
    img = flat(w, h, (245, 245, 240))
    for _ in range(n):
        x0, y0 = rng.integers(0, w - 1), rng.integers(0, h - 1)
        x1 = min(w, x0 + int(rng.integers(8, max(9, w // 4))))
        y1 = min(h, y0 + int(rng.integers(8, max(9, h // 4))))
        img[y0:y1, x0:x1] = rng.integers(0, 256, 3)
    return img


def noise(w: int, h: int, seed: int = 13) -> np.ndarray:
    """Ruído uniforme — o caso adversarial máximo (árvore degenera)."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def natural_proxy(w: int, h: int, seed: int = 21) -> np.ndarray:
    """Proxy de fotografia: campo suave multi-escala + detalhe fino.

    NÃO substitui o corpus natural real (spec §6) — serve aos testes de
    unidade do modo lossy enquanto o harness F4 usa fotos reais.
    """
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    for scale, amp in [(8, 90.0), (32, 50.0), (128, 25.0)]:
        gh, gw = max(2, h // scale), max(2, w // scale)
        coarse = rng.uniform(0, 1, (gh, gw, 3))
        ys = np.linspace(0, gh - 1, h)
        xs = np.linspace(0, gw - 1, w)
        y0 = np.floor(ys).astype(int)
        x0 = np.floor(xs).astype(int)
        y1 = np.minimum(y0 + 1, gh - 1)
        x1 = np.minimum(x0 + 1, gw - 1)
        fy = (ys - y0)[:, None, None]
        fx = (xs - x0)[None, :, None]
        top = coarse[y0][:, x0] * (1 - fx) + coarse[y0][:, x1] * fx
        bot = coarse[y1][:, x0] * (1 - fx) + coarse[y1][:, x1] * fx
        img += amp * (top * (1 - fy) + bot * fy)
    img += rng.normal(0, 3.0, (h, w, 3))  # ruído de sensor
    return np.clip(np.rint(img + 40), 0, 255).astype(np.uint8)


def load_image(path: str) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
