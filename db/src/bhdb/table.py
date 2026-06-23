"""Dataset sintético (log de eventos) + baselines de tabela plana.

Métrica: cada baseline reporta `rows_read` — as linhas que precisou tocar
para responder. É o análogo do "bytes lidos" do codec.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Table:
    key: np.ndarray        # int64, ordenado (timestamp monotónico)
    region: np.ndarray     # int8, categórico
    val_trend: np.ndarray  # float64, correlacionado com key
    val_rand: np.ndarray   # float64, independente da key

    def __len__(self) -> int:
        return len(self.key)


def make_dataset(n: int = 1_000_000, seed: int = 7, n_regions: int = 8) -> Table:
    rng = np.random.default_rng(seed)
    # chave: timestamps monotónicos com gaps irregulares
    gaps = rng.integers(1, 20, size=n, dtype=np.int64)
    key = np.cumsum(gaps)
    region = rng.integers(0, n_regions, size=n, dtype=np.int8)
    # val_trend: tendência crescente com a key + ruído → correlacionado
    trend = np.linspace(0.0, 1000.0, n) + rng.normal(0, 30.0, n)
    val_trend = trend.astype(np.float64)
    # val_rand: independente da key
    val_rand = rng.uniform(0.0, 1000.0, n).astype(np.float64)
    return Table(key=key, region=region, val_trend=val_trend, val_rand=val_rand)


# ---- baselines de tabela plana ----

def full_scan_sum(col: np.ndarray) -> tuple[float, dict]:
    return float(col.sum()), {"rows_read": len(col)}


def range_scan_sum(key: np.ndarray, col: np.ndarray, lo: int, hi: int) -> tuple[float, dict]:
    """Tabela ordenada: binary search + varre a fatia [lo, hi)."""
    r_lo = int(np.searchsorted(key, lo, "left"))
    r_hi = int(np.searchsorted(key, hi, "right"))
    return float(col[r_lo:r_hi].sum()), {"rows_read": r_hi - r_lo}


def filter_scan_count(col: np.ndarray, op: str, threshold: float) -> tuple[int, dict]:
    if op == "gt":
        m = col > threshold
    elif op == "lt":
        m = col < threshold
    else:
        raise ValueError(op)
    return int(m.sum()), {"rows_read": len(col)}


def filter_scan_eq_count(col: np.ndarray, value: int) -> tuple[int, dict]:
    return int((col == value).sum()), {"rows_read": len(col)}
