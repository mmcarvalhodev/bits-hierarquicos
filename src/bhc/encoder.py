"""BHC v0.2 — encoder: quadtree vetorizada com MULTI-INTERPRETAÇÃO por nó.

Cada nó escolhe a interpretação que melhor explica seu quadrante:
  LEAF      cor constante (3B)        — se o spread cabe no threshold
  RAMP      rampa bilinear (12B)      — se 4 cantos reproduzem o bloco
  INTERNAL  subdivide                 — quando nenhuma leitura barata serve
A hierarquia resultante é variável: adapta-se ao conteúdo (doc §4, o
campo "tipo de dado" do HEADER como selector de interpretação).

Sem recursão por nó: pirâmides min/max/mean/coverage por reduções 2×2,
ajuste de rampa só nos nós candidatos (gather + einsum).
"""
from __future__ import annotations

import numpy as np

from .format import (
    DCT, EMPTY, INTERNAL, LEAF, NOT_MAT, RAMP, Header, pack_level_table,
)
from . import dct
from .ramp import reconstruct as ramp_reconstruct


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def _reduce_2x2(a: np.ndarray, op: str) -> np.ndarray:
    """Reduz uma grade (2g, 2g[, C]) para (g, g[, C]) por blocos 2×2."""
    g = a.shape[0] // 2
    if a.ndim == 3:
        b = a.reshape(g, 2, g, 2, a.shape[2])
    else:
        b = a.reshape(g, 2, g, 2)
    if op == "min":
        return b.min(axis=(1, 3))
    if op == "max":
        return b.max(axis=(1, 3))
    if op == "mean":
        return b.mean(axis=(1, 3))
    raise ValueError(op)


def _corner_grids(padded: np.ndarray, s: int) -> np.ndarray:
    """Cantos de cada nó de lado s: (g, g, 4, 3) na ordem TL, TR, BL, BR."""
    return np.stack([
        padded[0::s, 0::s], padded[0::s, s - 1::s],
        padded[s - 1::s, 0::s], padded[s - 1::s, s - 1::s],
    ], axis=2)


def _ramp_fit(
    padded: np.ndarray, corners: np.ndarray, cand: np.ndarray,
    s: int, limit: float,
) -> np.ndarray:
    """Quais candidatos a rampa explica com erro máximo ≤ limit.

    Computado SÓ nos candidatos (gather), com a mesma reconstrução
    (rint + clip) que o decoder aplicará.
    """
    g = cand.shape[0]
    ok_mask = np.zeros((g, g), dtype=bool)
    ci, cj = np.nonzero(cand)
    if len(ci) == 0:
        return ok_mask
    rec = ramp_reconstruct(corners[ci, cj], s).astype(np.int16)
    img4 = padded.reshape(g, s, g, s, 3)
    sy = np.arange(s)
    blocks = img4[ci[:, None, None], sy[None, :, None], cj[:, None, None], sy[None, None, :]]
    err = np.abs(rec - blocks.astype(np.int16)).max(axis=(1, 2, 3))
    ok = err <= limit
    ok_mask[ci[ok], cj[ok]] = True
    return ok_mask


def _blocks_for_candidates(padded: np.ndarray, cand: np.ndarray, s: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    g = cand.shape[0]
    ci, cj = np.nonzero(cand)
    if len(ci) == 0:
        return ci, cj, np.empty((0, s, s, 3), dtype=np.uint8)
    img4 = padded.reshape(g, s, g, s, 3)
    sy = np.arange(s)
    blocks = img4[
        ci[:, None, None], sy[None, :, None],
        cj[:, None, None], sy[None, None, :],
    ]
    return ci, cj, blocks


def _dct_fit(
    padded: np.ndarray, cand: np.ndarray, s: int, limit: float,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Return DCT-fitting nodes and their serialized int16 coeff grids."""
    g = cand.shape[0]
    ok_mask = np.zeros((g, g), dtype=bool)
    coeff_grid: np.ndarray | None = None
    if s < 8 or s > 32:
        return ok_mask, coeff_grid
    ci, cj, blocks = _blocks_for_candidates(padded, cand, s)
    if len(ci) == 0:
        return ok_mask, coeff_grid
    coeff = dct.encode_blocks(blocks)
    rec = dct.reconstruct(coeff, s).astype(np.int16)
    err = np.abs(rec - blocks.astype(np.int16)).max(axis=(1, 2, 3))
    ok = err <= limit
    ok_mask[ci[ok], cj[ok]] = True
    if ok.any():
        coeff_grid = np.zeros((g, g, dct.COEFF_N, dct.COEFF_N, 3), dtype=np.int16)
        coeff_grid[ci[ok], cj[ok]] = coeff[ok]
    return ok_mask, coeff_grid


def encode(
    img: np.ndarray,
    *,
    lossy: bool = False,
    threshold: float = 0.0,
    pyramid: bool = True,
) -> tuple[bytes, dict]:
    """Codifica imagem RGB uint8 (H×W×3) para bytes BHC.

    Retorna (dados, stats). stats traz contadores por nível para o harness.
    """
    if img.ndim != 3 or img.shape[2] != 3 or img.dtype != np.uint8:
        raise ValueError("esperado array uint8 H×W×3 (RGB)")
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        raise ValueError("imagem vazia")

    size = _next_pow2(max(h, w))
    levels = int(size).bit_length() - 1  # N: grade folha = 2^N

    padded = np.zeros((size, size, 3), dtype=np.uint8)
    padded[:h, :w] = img
    inside = np.zeros((size, size), dtype=np.uint8)
    inside[:h, :w] = 2  # coverage: 0=fora, 1=parcial, 2=total

    # Pirâmides (índice k = nível, 0..N)
    mins: list[np.ndarray] = [None] * (levels + 1)  # type: ignore[list-item]
    maxs: list[np.ndarray] = [None] * (levels + 1)  # type: ignore[list-item]
    means: list[np.ndarray] = [None] * (levels + 1)  # type: ignore[list-item]
    cov: list[np.ndarray] = [None] * (levels + 1)  # type: ignore[list-item]
    mins[levels] = padded
    maxs[levels] = padded
    means[levels] = padded.astype(np.float64)
    cov[levels] = inside
    for k in range(levels - 1, -1, -1):
        mins[k] = _reduce_2x2(mins[k + 1], "min")
        maxs[k] = _reduce_2x2(maxs[k + 1], "max")
        means[k] = _reduce_2x2(means[k + 1], "mean")
        cmin = _reduce_2x2(cov[k + 1], "min")
        cmax = _reduce_2x2(cov[k + 1], "max")
        cov[k] = np.where(cmax == 0, 0, np.where(cmin == 2, 2, 1)).astype(np.uint8)

    def _homo(k: int) -> np.ndarray:
        if lossy:
            spread = maxs[k].astype(np.int16) - mins[k].astype(np.int16)
            return (spread <= threshold).all(axis=-1)
        return (mins[k] == maxs[k]).all(axis=-1)

    ramp_limit = threshold if lossy else 0.0

    # Tipos top-down — seleção de interpretação por nó
    types: list[np.ndarray] = []
    corners: list[np.ndarray | None] = [None] * (levels + 1)
    dct_coeffs: list[np.ndarray | None] = [None] * (levels + 1)
    homo0 = bool(_homo(0)[0, 0]) or levels == 0
    if homo0:
        root = LEAF
    else:
        s0 = size
        corners[0] = _corner_grids(padded, s0)
        ok0 = _ramp_fit(padded, corners[0], np.ones((1, 1), bool), s0, ramp_limit)
        root = RAMP if ok0[0, 0] else INTERNAL
    types.append(np.array([[root]], dtype=np.uint8))

    for k in range(1, levels + 1):
        parent_internal = types[k - 1] == INTERNAL
        pmask = np.repeat(np.repeat(parent_internal, 2, axis=0), 2, axis=1)
        s = size >> k
        homo_k = _homo(k)
        t = np.where(
            cov[k] == 0, EMPTY,
            np.where(homo_k | (k == levels), LEAF, INTERNAL),
        ).astype(np.uint8)
        if s >= 2:
            cand = pmask & (cov[k] != 0) & ~homo_k
            if cand.any():
                corners[k] = _corner_grids(padded, s)
                ok = _ramp_fit(padded, corners[k], cand, s, ramp_limit)
                t = np.where(ok, RAMP, t).astype(np.uint8)
        types.append(np.where(pmask, t, NOT_MAT).astype(np.uint8))

    def _payload_sizes(k: int) -> np.ndarray:
        t = types[k]
        sizes = np.zeros(t.shape, dtype=np.int64)
        sizes[t == LEAF] = 3
        if pyramid:
            sizes[t == INTERNAL] = 3
        sizes[t == RAMP] = 12
        sizes[t == DCT] = dct.PAYLOAD_BYTES
        return sizes

    def _estimated_total_bytes(wide: bool) -> int:
        total = Header(
            width=w, height=h, levels=levels,
            lossy=lossy, pyramid=pyramid, wide_types=wide,
            threshold=float(threshold), root_type=int(types[0][0, 0]),
        ).pack().__len__() + len(pack_level_table([(0, 0)] * (levels + 1)))
        for kk in range(levels + 1):
            if kk > 0:
                n_parents = int((types[kk - 1] == INTERNAL).sum())
                total += n_parents * (4 if wide else 1)
            total += int(_payload_sizes(kk).sum())
        return total

    def _prune_subtree(k: int, i: int, j: int) -> None:
        for m in range(k + 1, levels + 1):
            scale = 2 ** (m - k)
            types[m][i * scale:(i + 1) * scale, j * scale:(j + 1) * scale] = NOT_MAT

    wide_types = False
    if lossy:
        baseline_types = [t.copy() for t in types]
        baseline_total = _estimated_total_bytes(wide=False)
        # Rate-distortion first cut: DCT is accepted only when its fixed
        # payload is cheaper than the already-built subtree it would replace.
        cost_maps: list[np.ndarray | None] = [None] * (levels + 1)
        for k in range(levels, -1, -1):
            if k == levels:
                cost_k = _payload_sizes(k)
            else:
                g = 2**k
                child = cost_maps[k + 1]
                assert child is not None
                child_sum = child.reshape(g, 2, g, 2).sum(axis=(1, 3))
                # Local decision is against the compact tree cost. The global
                # wide_types guard below rejects DCT if wider structure loses.
                cost_k = _payload_sizes(k) + np.where(types[k] == INTERNAL, 1 + child_sum, 0)

            s = size >> k
            cand = types[k] == INTERNAL
            if not cand.any() or s < 8 or s > 32:
                cost_maps[k] = cost_k
                continue
            ok_dct, coeff = _dct_fit(padded, cand, s, ramp_limit)
            if not ok_dct.any():
                cost_maps[k] = cost_k
                continue
            if dct_coeffs[k] is None:
                dct_coeffs[k] = np.zeros((2**k, 2**k, dct.COEFF_N, dct.COEFF_N, 3), dtype=np.int16)
            ci, cj = np.nonzero(ok_dct)
            for i, j in zip(ci, cj):
                if types[k][i, j] != INTERNAL:
                    continue
                old_cost = int(cost_k[i, j])
                new_cost = dct.PAYLOAD_BYTES
                if old_cost > new_cost:
                    types[k][i, j] = DCT
                    dct_coeffs[k][i, j] = coeff[i, j]
                    cost_k[i, j] = new_cost
                    _prune_subtree(k, int(i), int(j))
            cost_maps[k] = cost_k
        wide_total = _estimated_total_bytes(wide=True)
        if sum(int((t == DCT).sum()) for t in types) > 0 and wide_total < baseline_total:
            wide_types = True
        else:
            types = baseline_types
            dct_coeffs = [None] * (levels + 1)

    def _leaf_colors(k: int) -> np.ndarray:
        if lossy:
            return np.clip(np.rint(means[k]), 0, 255).astype(np.uint8)
        return mins[k]

    def _mean_colors(k: int) -> np.ndarray:
        return np.clip(np.rint(means[k]), 0, 255).astype(np.uint8)

    # Serialização por nível: [STRUCTURE][DATA] — payloads de tamanho
    # variável (LEAF/média 3B, RAMP 12B) em ordem row-major
    sections: list[tuple[bytes, bytes]] = []
    stats_levels = []
    for k in range(levels + 1):
        if k == 0:
            struct_bytes = b""  # tipo da raiz vive no header
        else:
            g = 2 ** (k - 1)
            blocks = (
                types[k].reshape(g, 2, g, 2)
                .transpose(0, 2, 1, 3)
                .reshape(g * g, 4)
                .astype(np.uint8)
            )
            sel = blocks[(types[k - 1] == INTERNAL).ravel()]
            if wide_types:
                struct_bytes = sel.tobytes()
            else:
                packed = (
                    sel[:, 0].astype(np.uint16)
                    | (sel[:, 1].astype(np.uint16) << 2)
                    | (sel[:, 2].astype(np.uint16) << 4)
                    | (sel[:, 3].astype(np.uint16) << 6)
                ).astype(np.uint8)
                struct_bytes = packed.tobytes()

        leaf_mask = types[k] == LEAF
        ramp_mask = types[k] == RAMP
        dct_mask = types[k] == DCT
        internal_mask = types[k] == INTERNAL
        gk = 2**k

        sizes = np.zeros((gk, gk), dtype=np.int64)
        sizes[leaf_mask] = 3
        if pyramid:
            sizes[internal_mask] = 3
        sizes[ramp_mask] = 12
        sizes[dct_mask] = dct.PAYLOAD_BYTES
        flat_sizes = sizes.ravel()
        offs = (np.cumsum(flat_sizes) - flat_sizes).reshape(gk, gk)
        buf = np.zeros(int(flat_sizes.sum()), dtype=np.uint8)

        m3 = sizes == 3
        if m3.any():
            vals3 = np.zeros((gk, gk, 3), dtype=np.uint8)
            if leaf_mask.any():
                vals3[leaf_mask] = _leaf_colors(k)[leaf_mask]
            if pyramid and internal_mask.any():
                vals3[internal_mask] = _mean_colors(k)[internal_mask]
            buf[offs[m3][:, None] + np.arange(3)] = vals3[m3]
        if ramp_mask.any():
            assert corners[k] is not None
            rvals = corners[k][ramp_mask].reshape(-1, 12)
            buf[offs[ramp_mask][:, None] + np.arange(12)] = rvals
        if dct_mask.any():
            assert dct_coeffs[k] is not None
            dvals = (
                dct_coeffs[k][dct_mask]
                .astype("<i2", copy=False)
                .reshape(-1, dct.COEFF_N * dct.COEFF_N * 3)
                .view(np.uint8)
                .reshape(-1, dct.PAYLOAD_BYTES)
            )
            buf[offs[dct_mask][:, None] + np.arange(dct.PAYLOAD_BYTES)] = (
                dvals
            )
        data_bytes = buf.tobytes()

        sections.append((struct_bytes, data_bytes))
        stats_levels.append({
            "level": k,
            "leaves": int(leaf_mask.sum()),
            "ramps": int(ramp_mask.sum()),
            "dct": int(dct_mask.sum()),
            "internal": int(internal_mask.sum()),
            "empty": int((types[k] == EMPTY).sum()),
            "struct_bytes": len(struct_bytes),
            "data_bytes": len(data_bytes),
        })

    header = Header(
        width=w, height=h, levels=levels,
        lossy=lossy, pyramid=pyramid,
        wide_types=wide_types,
        threshold=float(threshold),
        root_type=int(types[0][0, 0]),
    )
    table = pack_level_table([(len(s), len(d)) for s, d in sections])
    body = b"".join(s + d for s, d in sections)
    blob = header.pack() + table + body

    stats = {
        "padded_size": size,
        "levels": levels,
        "total_bytes": len(blob),
        "raw_bytes": h * w * 3,
        "wide_types": wide_types,
        "total_leaves": sum(s["leaves"] for s in stats_levels),
        "total_ramps": sum(s["ramps"] for s in stats_levels),
        "total_dct": sum(s["dct"] for s in stats_levels),
        "total_internal": sum(s["internal"] for s in stats_levels),
        "per_level": stats_levels,
    }
    return blob, stats
