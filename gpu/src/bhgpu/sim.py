"""Simulação de movimento de dados — workload GPU intensivo, flat vs BH.

Mede bytes movidos da DRAM + linhas de cache, NÃO desempenho de GPU real.
Penaliza o BH por acesso espalhado (cada nó tocado = 1 linha de cache).
A ponte para tempo (bytes / largura de banda) só vale bandwidth-bound.
"""
from __future__ import annotations

import numpy as np

CACHE_LINE = 128          # bytes
ELEM = 4                  # float32
NODE = 16                 # sum+min+max (f32) + count (u32)
BANDWIDTH = 3.35e12       # B/s — HBM3 classe H100 (só p/ estimar tempo)
BLOCK = 32                # elementos por bloco-folha = 1 linha de cache


def _lines(nbytes: int) -> int:
    return -(-nbytes // CACHE_LINE)  # ceil


class HierArray:
    """Array grande + pirâmide de agregados (sum/min/max/count) por bloco.

    Vetorizado: níveis construídos por reduções; sem árvore de objetos.
    """

    def __init__(self, values: np.ndarray):
        assert values.ndim == 1
        self.values = values.astype(np.float64)
        self.n = values.size
        self.n_blocks = -(-self.n // BLOCK)
        size = 1
        while size < self.n_blocks:
            size *= 2
        self.size = size
        # agregados por bloco
        bsum = np.zeros(size); bmin = np.full(size, np.inf)
        bmax = np.full(size, -np.inf); bcnt = np.zeros(size, np.int64)
        for b in range(self.n_blocks):
            s, e = b * BLOCK, min((b + 1) * BLOCK, self.n)
            v = self.values[s:e]
            bsum[b] = v.sum(); bmin[b] = v.min(); bmax[b] = v.max(); bcnt[b] = e - s
        # segment tree 1-indexed
        P = size
        self.tsum = np.zeros(2 * P); self.tmin = np.full(2 * P, np.inf)
        self.tmax = np.full(2 * P, -np.inf); self.tcnt = np.zeros(2 * P, np.int64)
        self.tsum[P:2 * P] = bsum; self.tmin[P:2 * P] = bmin
        self.tmax[P:2 * P] = bmax; self.tcnt[P:2 * P] = bcnt
        for i in range(P - 1, 0, -1):
            l, r = 2 * i, 2 * i + 1
            self.tsum[i] = self.tsum[l] + self.tsum[r]
            self.tmin[i] = min(self.tmin[l], self.tmin[r])
            self.tmax[i] = max(self.tmax[l], self.tmax[r])
            self.tcnt[i] = self.tcnt[l] + self.tcnt[r]
        self.levels = size.bit_length()

    # ---------- Q1: agregação de range ----------

    def range_sum_flat_bytes(self, lo: int, hi: int) -> int:
        first = lo // BLOCK
        last = (hi - 1) // BLOCK
        # leitura contígua coalescida: linhas que cobrem [lo,hi)
        return _lines((hi - lo) * ELEM) * CACHE_LINE

    def range_sum_bh(self, lo: int, hi: int) -> tuple[float, int]:
        """Retorna (soma, bytes_movidos). Nós cobertos + 2 blocos fronteira."""
        b_lo, b_hi = lo // BLOCK, (hi - 1) // BLOCK
        acc = 0.0
        nodes = 0
        boundary_lines = 0
        if b_lo == b_hi:
            acc += self.values[lo:hi].sum()
            return acc, _lines((hi - lo) * ELEM) * CACHE_LINE
        # fronteiras: blocos crus
        acc += self.values[lo:(b_lo + 1) * BLOCK].sum()
        acc += self.values[b_hi * BLOCK:hi].sum()
        boundary_lines = 2  # 2 blocos = 2 linhas
        # miolo via segment tree
        il, ih = b_lo + 1, b_hi - 1
        if il <= ih:
            P = self.size
            l = il + P; r = ih + P + 1
            while l < r:
                if l & 1:
                    acc += self.tsum[l]; nodes += 1; l += 1
                if r & 1:
                    r -= 1; acc += self.tsum[r]; nodes += 1
                l >>= 1; r >>= 1
        # penalidade de scatter: cada nó tocado = 1 linha de cache inteira
        bytes_bh = (nodes + boundary_lines) * CACHE_LINE
        return acc, bytes_bh

    # ---------- Q2: level-of-detail (passada grosseira) ----------

    def lod_flat_bytes(self) -> int:
        return _lines(self.n * ELEM) * CACHE_LINE  # tem de varrer tudo

    def lod_bh_bytes(self, top_levels: int) -> int:
        # lê os nós dos níveis do topo (contíguos por nível)
        nodes = 2 ** top_levels - 1
        return _lines(nodes * NODE) * CACHE_LINE

    # ---------- Q4: filtro com poda ----------

    def filter_flat_bytes(self) -> int:
        return _lines(self.n * ELEM) * CACHE_LINE

    def filter_bh_bytes(self, threshold: float) -> tuple[int, int]:
        """Conta linhas movidas podando por max. Retorna (count, bytes)."""
        P = self.size
        count = 0
        nodes_touched = 0
        block_lines = 0
        stack = [1]
        while stack:
            node = stack.pop()
            nodes_touched += 1
            if self.tcnt[node] == 0 or self.tmax[node] <= threshold:
                continue
            if node >= P:
                b = node - P
                s, e = b * BLOCK, min((b + 1) * BLOCK, self.n)
                count += int((self.values[s:e] > threshold).sum())
                block_lines += 1  # 1 bloco = 1 linha
            else:
                stack.append(2 * node); stack.append(2 * node + 1)
        bytes_bh = (nodes_touched + block_lines) * CACHE_LINE
        return count, bytes_bh


def context_coupled(n_items: int) -> dict:
    """Q3: cada item precisa do valor + seu contexto/agregado.

    flat: valor (1 linha) + contexto em outro array (1 linha scattered) = 2/item.
    bh:   contexto embutido adjacente → 1 linha cobre ~BLOCK itens + agregado.
    """
    flat_bytes = n_items * 2 * CACHE_LINE
    # bh: itens agrupados por bloco; cada bloco (1 linha) traz BLOCK valores +
    # o agregado do pai amortizado. ~1 linha por BLOCK itens.
    bh_bytes = _lines(n_items / BLOCK) * CACHE_LINE if n_items >= BLOCK else CACHE_LINE
    bh_bytes = -(-n_items // BLOCK) * CACHE_LINE
    return {"flat": flat_bytes, "bh": bh_bytes}
