"""AggregateTree — segment tree sobre blocos de linhas (análogo 1D da
pirâmide do codec). A MESMA árvore é lida de três formas diferentes,
cada uma escolhida pelo objetivo da query — a "biblioteca de
interpretações" do paradigma, em banco de dados.

Instrumentação: toda leitura reporta `rows_read` (linhas cruas tocadas) e
`nodes_read` (nós de agregado consultados). `rows_read` é a métrica
headline — o análogo do "bytes lidos" do codec.
"""
from __future__ import annotations

import numpy as np

from .table import Table


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


class AggregateTree:
    """Segment tree binário sobre blocos de B linhas.

    Cada nó carrega sum/min/max/count de UMA coluna de valor + key_min/max
    para poda por range de chave. Construído para `col` (val_trend por
    defeito); key sempre disponível para range.
    """

    def __init__(self, table: Table, col: str = "val_trend", block: int = 1024):
        self.table = table
        self.col = col
        self.block = block
        self.n = len(table)
        self.values = getattr(table, col)
        self.key = table.key
        self.n_regions = int(table.region.max()) + 1 if self.n else 0

        self.n_blocks = -(-self.n // block)        # ceil
        self.size = _next_pow2(self.n_blocks)      # folhas do segtree (padded)

        # agregados por bloco (folhas)
        bsum = np.zeros(self.size, dtype=np.float64)
        bmin = np.full(self.size, np.inf)
        bmax = np.full(self.size, -np.inf)
        bcnt = np.zeros(self.size, dtype=np.int64)
        bkmin = np.full(self.size, np.iinfo(np.int64).max, dtype=np.int64)
        bkmax = np.full(self.size, np.iinfo(np.int64).min, dtype=np.int64)
        bregion_counts = np.zeros((self.size, self.n_regions), dtype=np.int64)
        for b in range(self.n_blocks):
            s, e = b * block, min((b + 1) * block, self.n)
            v = self.values[s:e]
            bsum[b] = v.sum()
            bmin[b] = v.min()
            bmax[b] = v.max()
            bcnt[b] = e - s
            bkmin[b] = self.key[s]
            bkmax[b] = self.key[e - 1]
            bregion_counts[b] = np.bincount(
                self.table.region[s:e], minlength=self.n_regions,
            )

        # segment tree em array 1-indexed: nós [1..2*size-1]
        P = self.size
        self.tsum = np.zeros(2 * P, dtype=np.float64)
        self.tmin = np.full(2 * P, np.inf)
        self.tmax = np.full(2 * P, -np.inf)
        self.tcnt = np.zeros(2 * P, dtype=np.int64)
        self.tkmin = np.full(2 * P, np.iinfo(np.int64).max, dtype=np.int64)
        self.tkmax = np.full(2 * P, np.iinfo(np.int64).min, dtype=np.int64)
        self.tregion_counts = np.zeros((2 * P, self.n_regions), dtype=np.int64)
        # folhas
        self.tsum[P:P + P] = bsum
        self.tmin[P:P + P] = bmin
        self.tmax[P:P + P] = bmax
        self.tcnt[P:P + P] = bcnt
        self.tkmin[P:P + P] = bkmin
        self.tkmax[P:P + P] = bkmax
        self.tregion_counts[P:P + P] = bregion_counts
        # subir
        for i in range(P - 1, 0, -1):
            l, r = 2 * i, 2 * i + 1
            self.tsum[i] = self.tsum[l] + self.tsum[r]
            self.tmin[i] = min(self.tmin[l], self.tmin[r])
            self.tmax[i] = max(self.tmax[l], self.tmax[r])
            self.tcnt[i] = self.tcnt[l] + self.tcnt[r]
            self.tkmin[i] = min(self.tkmin[l], self.tkmin[r])
            self.tkmax[i] = max(self.tkmax[l], self.tkmax[r])
            self.tregion_counts[i] = self.tregion_counts[l] + self.tregion_counts[r]

        self.depth = self.size.bit_length()  # níveis do segtree
        self.value_stats = {
            self.col: {
                "sum": self.tsum,
                "min": self.tmin,
                "max": self.tmax,
                "count": self.tcnt,
            }
        }
        for name in ("val_trend", "val_rand"):
            if name != self.col and hasattr(table, name):
                self.value_stats[name] = self._build_value_stats(getattr(table, name))

    def _build_value_stats(self, values: np.ndarray) -> dict[str, np.ndarray]:
        """Build sum/min/max trees for another numeric interpretation."""
        bsum = np.zeros(self.size, dtype=np.float64)
        bmin = np.full(self.size, np.inf)
        bmax = np.full(self.size, -np.inf)
        bcnt = np.zeros(self.size, dtype=np.int64)
        for b in range(self.n_blocks):
            s, e = b * self.block, min((b + 1) * self.block, self.n)
            v = values[s:e]
            bsum[b] = v.sum()
            bmin[b] = v.min()
            bmax[b] = v.max()
            bcnt[b] = e - s

        P = self.size
        tsum = np.zeros(2 * P, dtype=np.float64)
        tmin = np.full(2 * P, np.inf)
        tmax = np.full(2 * P, -np.inf)
        tcnt = np.zeros(2 * P, dtype=np.int64)
        tsum[P:P + P] = bsum
        tmin[P:P + P] = bmin
        tmax[P:P + P] = bmax
        tcnt[P:P + P] = bcnt
        for i in range(P - 1, 0, -1):
            l, r = 2 * i, 2 * i + 1
            tsum[i] = tsum[l] + tsum[r]
            tmin[i] = min(tmin[l], tmin[r])
            tmax[i] = max(tmax[l], tmax[r])
            tcnt[i] = tcnt[l] + tcnt[r]
        return {"sum": tsum, "min": tmin, "max": tmax, "count": tcnt}

    # ---- interpretação 1: AGREGADO (≈ thumbnail) ----

    def aggregate_range(self, lo: int, hi: int) -> tuple[dict, dict]:
        """SUM/COUNT/MIN/MAX de `col` onde key in [lo, hi].

        Usa nós cobertos para o miolo; lê linhas cruas só nos 2 blocos de
        fronteira. Retorna (resultado, stats).
        """
        r_lo = int(np.searchsorted(self.key, lo, "left"))
        r_hi = int(np.searchsorted(self.key, hi, "right"))
        rows_read = 0
        nodes_read = 0
        acc_sum = 0.0
        acc_cnt = 0
        acc_min = np.inf
        acc_max = -np.inf

        if r_hi <= r_lo:
            return ({"sum": 0.0, "count": 0, "min": None, "max": None},
                    {"rows_read": 0, "nodes_read": 0})

        b_lo = r_lo // self.block
        b_hi = (r_hi - 1) // self.block

        def read_raw(s: int, e: int):
            nonlocal rows_read, acc_sum, acc_cnt, acc_min, acc_max
            v = self.values[s:e]
            rows_read += e - s
            acc_sum += float(v.sum())
            acc_cnt += e - s
            if len(v):
                acc_min = min(acc_min, float(v.min()))
                acc_max = max(acc_max, float(v.max()))

        if b_lo == b_hi:
            read_raw(r_lo, r_hi)
        else:
            # blocos de fronteira: leitura crua
            read_raw(r_lo, (b_lo + 1) * self.block)
            read_raw(b_hi * self.block, r_hi)
            # miolo: blocos [b_lo+1, b_hi-1] via segment tree (sem ler linhas)
            inner_lo, inner_hi = b_lo + 1, b_hi - 1
            if inner_lo <= inner_hi:
                P = self.size
                l = inner_lo + P
                r = inner_hi + P + 1  # exclusivo
                while l < r:
                    if l & 1:
                        acc_sum += self.tsum[l]; acc_cnt += int(self.tcnt[l])
                        acc_min = min(acc_min, self.tmin[l])
                        acc_max = max(acc_max, self.tmax[l])
                        nodes_read += 1
                        l += 1
                    if r & 1:
                        r -= 1
                        acc_sum += self.tsum[r]; acc_cnt += int(self.tcnt[r])
                        acc_min = min(acc_min, self.tmin[r])
                        acc_max = max(acc_max, self.tmax[r])
                        nodes_read += 1
                    l >>= 1
                    r >>= 1

        res = {
            "sum": acc_sum, "count": acc_cnt,
            "min": (None if acc_min == np.inf else acc_min),
            "max": (None if acc_max == -np.inf else acc_max),
        }
        return res, {"rows_read": rows_read, "nodes_read": nodes_read}

    def aggregate_global(self) -> tuple[dict, dict]:
        """Agregado da tabela inteira: lê só a raiz."""
        return ({"sum": float(self.tsum[1]), "count": int(self.tcnt[1]),
                 "min": float(self.tmin[1]), "max": float(self.tmax[1])},
                {"rows_read": 0, "nodes_read": 1})

    # ---- interpretação 2: PODA (≈ ROI) ----

    def prune_filter_count(self, op: str, threshold: float) -> tuple[int, dict]:
        return self.prune_filter_count_col(self.col, op, threshold)

    def prune_filter_count_col(self, col: str, op: str, threshold: float) -> tuple[int, dict]:
        """COUNT de linhas onde `col` op threshold, podando por min/max.

        op: 'gt' (val_max <= t poda) ou 'lt' (val_min >= t poda).
        Lê linhas cruas só nos blocos que sobrevivem à poda.
        """
        rows_read = 0
        nodes_read = 0
        count = 0
        P = self.size
        if col not in self.value_stats:
            raise ValueError(f"coluna sem estatistica materializada: {col}")
        values = getattr(self.table, col)
        stats = self.value_stats[col]
        tmin = stats["min"]
        tmax = stats["max"]
        tcnt = stats["count"]

        def can_skip(node: int) -> bool:
            if tcnt[node] == 0:
                return True
            if op == "gt":
                return tmax[node] <= threshold
            if op == "lt":
                return tmin[node] >= threshold
            raise ValueError(op)

        stack = [1]
        while stack:
            node = stack.pop()
            nodes_read += 1
            if can_skip(node):
                continue
            if node >= P:  # folha = bloco
                b = node - P
                s, e = b * self.block, min((b + 1) * self.block, self.n)
                v = values[s:e]
                rows_read += e - s
                count += int((v > threshold).sum() if op == "gt"
                             else (v < threshold).sum())
            else:
                stack.append(2 * node)
                stack.append(2 * node + 1)
        return count, {"rows_read": rows_read, "nodes_read": nodes_read}

    def prune_range_count(self, lo: int, hi: int) -> tuple[int, dict]:
        """COUNT de linhas com key in [lo, hi] — poda por key_min/max."""
        rows_read = 0
        nodes_read = 0
        count = 0
        P = self.size
        stack = [1]
        while stack:
            node = stack.pop()
            nodes_read += 1
            if self.tcnt[node] == 0 or self.tkmax[node] < lo or self.tkmin[node] > hi:
                continue
            if lo <= self.tkmin[node] and self.tkmax[node] <= hi:
                count += int(self.tcnt[node])  # bloco/subárvore inteiramente dentro
                continue
            if node >= P:
                b = node - P
                s, e = b * self.block, min((b + 1) * self.block, self.n)
                k = self.key[s:e]
                rows_read += e - s
                count += int(((k >= lo) & (k <= hi)).sum())
            else:
                stack.append(2 * node)
                stack.append(2 * node + 1)
        return count, {"rows_read": rows_read, "nodes_read": nodes_read}

    # ---- interpretação 3: SCAN CRU (o baseline dentro do BH) ----

    # ---- interpretacao 2b: AGREGACAO CATEGORICA ----

    def region_count(self, region_value: int) -> tuple[int, dict]:
        """COUNT region == value usando contadores por regiao na raiz."""
        if not (0 <= region_value < self.n_regions):
            return 0, {"rows_read": 0, "nodes_read": 1}
        return (
            int(self.tregion_counts[1, region_value]),
            {"rows_read": 0, "nodes_read": 1},
        )

    def region_count_range(self, region_value: int, lo: int, hi: int) -> tuple[int, dict]:
        """COUNT region == value AND key in [lo, hi]."""
        if not (0 <= region_value < self.n_regions):
            return 0, {"rows_read": 0, "nodes_read": 0}

        r_lo = int(np.searchsorted(self.key, lo, "left"))
        r_hi = int(np.searchsorted(self.key, hi, "right"))
        if r_hi <= r_lo:
            return 0, {"rows_read": 0, "nodes_read": 0}

        rows_read = 0
        nodes_read = 0
        count = 0
        b_lo = r_lo // self.block
        b_hi = (r_hi - 1) // self.block

        def read_raw(s: int, e: int) -> None:
            nonlocal rows_read, count
            rows_read += e - s
            count += int((self.table.region[s:e] == region_value).sum())

        if b_lo == b_hi:
            read_raw(r_lo, r_hi)
        else:
            read_raw(r_lo, (b_lo + 1) * self.block)
            read_raw(b_hi * self.block, r_hi)
            inner_lo, inner_hi = b_lo + 1, b_hi - 1
            if inner_lo <= inner_hi:
                P = self.size
                l = inner_lo + P
                r = inner_hi + P + 1
                while l < r:
                    if l & 1:
                        count += int(self.tregion_counts[l, region_value])
                        nodes_read += 1
                        l += 1
                    if r & 1:
                        r -= 1
                        count += int(self.tregion_counts[r, region_value])
                        nodes_read += 1
                    l >>= 1
                    r >>= 1
        return count, {"rows_read": rows_read, "nodes_read": nodes_read}

    def raw_scan_sum(self) -> tuple[float, dict]:
        total = 0.0
        for b in range(self.n_blocks):
            s, e = b * self.block, min((b + 1) * self.block, self.n)
            total += float(self.values[s:e].sum())
        return total, {"rows_read": self.n, "nodes_read": 0}

    def off_axis_region_count(self, region_value: int) -> tuple[int, dict]:
        """Filtro por região: a árvore NÃO agrega região → SEM poda possível.
        Demonstra D3: lê todos os blocos + overhead de visitar a árvore."""
        rows_read = 0
        nodes_read = 0
        count = 0
        for b in range(self.n_blocks):
            nodes_read += 1  # overhead: ainda visita o nó-bloco
            s, e = b * self.block, min((b + 1) * self.block, self.n)
            reg = self.table.region[s:e]
            rows_read += e - s
            count += int((reg == region_value).sum())
        return count, {"rows_read": rows_read, "nodes_read": nodes_read}
