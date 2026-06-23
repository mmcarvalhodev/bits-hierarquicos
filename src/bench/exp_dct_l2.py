"""EXPERIMENTO — testa o diagnóstico: o gargalo do DCT é a métrica de fit?

Troca o critério L∞ (erro máximo) por L2 (RMSE) via monkeypatch, SEM tocar
no encoder do GPT. Mede se o DCT passa a disparar e a fechar o gap da foto
natural contra o WebP a PSNR equivalente.

Caveat de honestidade: sob L2, nós DCT podem exceder o erro-máximo =
threshold (o contrato de erro-máximo deixa de valer para esses nós — é
exatamente o que JPEG/WebP fazem). O que medimos é PSNR vs tamanho.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from PIL import Image

import bhc.encoder as enc
from bhc import dct
from bhc.metrics import psnr


def dct_fit_l2(padded, cand, s, limit):
    """Igual ao _dct_fit do encoder, mas com critério RMSE em vez de máximo."""
    g = cand.shape[0]
    ok_mask = np.zeros((g, g), dtype=bool)
    coeff_grid = None
    if s < 8 or s > 32:
        return ok_mask, coeff_grid
    ci, cj, blocks = enc._blocks_for_candidates(padded, cand, s)
    if len(ci) == 0:
        return ok_mask, coeff_grid
    coeff = dct.encode_blocks(blocks)
    rec = dct.reconstruct(coeff, s).astype(np.int16)
    diff = (rec - blocks.astype(np.int16)).astype(np.float64)
    rmse = np.sqrt((diff ** 2).mean(axis=(1, 2, 3)))
    ok = rmse <= limit
    ok_mask[ci[ok], cj[ok]] = True
    if ok.any():
        coeff_grid = np.zeros((g, g, dct.COEFF_N, dct.COEFF_N, 3), dtype=np.int16)
        coeff_grid[ci[ok], cj[ok]] = coeff[ok]
    return ok_mask, coeff_grid


def webp_at(img, target):
    pil = Image.fromarray(img)
    best = None
    for q in range(5, 96, 5):
        b = io.BytesIO(); pil.save(b, "WEBP", quality=q)
        dec = np.asarray(Image.open(io.BytesIO(b.getvalue())).convert("RGB"))
        p = psnr(img, dec)
        if best is None or abs(p - target) < abs(best[2] - target):
            best = (q, b.tell(), p)
    return best


def load(name):
    return np.asarray(Image.open(ROOT / f"data/corpus/{name}.jpg").convert("RGB"),
                      dtype=np.uint8)


def measure(name, thresholds=(8.0, 16.0, 24.0)):
    img = load(name)
    print(f"=== {name} ===")
    print(f"{'thr':>4} {'crit':>5} {'BH(MB)':>8} {'PSNR':>6} {'WebP(MB)':>9} "
          f"{'BH/WebP':>8} {'dct':>7} {'ramp':>8}")
    for t in thresholds:
        for label, patch in [("Linf", enc._dct_fit), ("L2", dct_fit_l2)]:
            orig = enc._dct_fit
            enc._dct_fit = patch
            try:
                blob, st = enc.encode(img, lossy=True, threshold=t, pyramid=False)
            finally:
                enc._dct_fit = orig
            from bhc import decode_full
            out, _ = decode_full(blob)
            p = psnr(img, out)
            _, wsize, _ = webp_at(img, p)
            print(f"{t:4.0f} {label:>5} {len(blob)/1e6:8.3f} {p:6.1f} "
                  f"{wsize/1e6:9.3f} {len(blob)/wsize:7.1f}x "
                  f"{st.get('total_dct', 0):7,} {st.get('total_ramps', 0):8,}")


if __name__ == "__main__":
    for name in ["natural_city", "natural_forest", "natural_portrait"]:
        measure(name)
