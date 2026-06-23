"""Sanity check F1 em 4K — tamanhos, tempos e bit-exactness por classe."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from bench import corpus
from bhc import decode_full, encode

W, H = 3840, 2160
cases = [
    ("flat", corpus.flat(W, H)),
    ("shapes", corpus.shapes(W, H)),
    ("gradient", corpus.gradient(W, H)),
    ("noise", corpus.noise(W, H)),
]

for name, img in cases:
    raw = img.nbytes
    t0 = time.perf_counter()
    blob, st = encode(img, pyramid=True)
    t1 = time.perf_counter()
    out, info = decode_full(blob)
    t2 = time.perf_counter()
    ok = np.array_equal(out, img)
    print(
        f"{name:9s} raw={raw / 1e6:7.1f}MB  bhc={len(blob) / 1e6:8.3f}MB  "
        f"ratio={len(blob) / raw:7.4f}  folhas={st['total_leaves']:>9,}  "
        f"enc={t1 - t0:5.2f}s  dec={t2 - t1:5.2f}s  bitexact={ok}"
    )
