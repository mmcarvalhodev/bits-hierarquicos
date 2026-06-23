"""BHC v0.2 — decoders: full, progressive e ROI, com multi-interpretação.

Reconstrói os tipos por nível a partir das seções de estrutura (a posição
de cada nó é derivada da ordenação BFS/row-major — hierarquia como
interpretação da posição no stream) e pinta cada folha segundo a
interpretação declarada no seu código de 2 bits: LEAF = cor constante,
RAMP = rampa bilinear de 4 cantos.

Instrumentação: todo decoder reporta bytes lidos — é a medida das
alegações C1 (progressivo) e C2 (ROI) da spec.
"""
from __future__ import annotations

import numpy as np

from .format import (
    DCT, HEADER_SIZE, INTERNAL, LEAF, NOT_MAT, RAMP, Header,
    level_table_size, unpack_level_table,
)
from . import dct
from .ramp import reconstruct as ramp_reconstruct


def _unpack_children(
    struct_bytes: bytes, parent_internal: np.ndarray, wide_types: bool = False,
) -> np.ndarray:
    """Reconstrói a grade de tipos do nível k a partir da estrutura."""
    g = parent_internal.shape[0]
    n_parents = int(parent_internal.sum())
    raw = np.frombuffer(struct_bytes, dtype=np.uint8)
    expected = n_parents * (4 if wide_types else 1)
    if len(raw) != expected:
        raise ValueError(
            f"estrutura corrompida: {len(raw)} bytes para {n_parents} pais internos"
        )
    if wide_types:
        children = raw.reshape(n_parents, 4)
    else:
        children = np.stack([(raw >> (2 * i)) & 3 for i in range(4)], axis=1)
    blocks = np.full((g * g, 4), NOT_MAT, dtype=np.uint8)
    blocks[parent_internal.ravel()] = children
    return (
        blocks.reshape(g, g, 2, 2).transpose(0, 2, 1, 3).reshape(2 * g, 2 * g)
    )


def _payload_layout(types_k: np.ndarray, pyramid: bool):
    """Máscaras + tamanhos + offsets dos payloads do nível (ordem row-major)."""
    leaf = types_k == LEAF
    ramp = types_k == RAMP
    dct_mask = types_k == DCT
    internal = types_k == INTERNAL
    sizes = np.zeros(types_k.shape, dtype=np.int64)
    sizes[leaf] = 3
    if pyramid:
        sizes[internal] = 3
    sizes[ramp] = 12
    sizes[dct_mask] = dct.PAYLOAD_BYTES
    flat = sizes.ravel()
    offs = (np.cumsum(flat) - flat).reshape(types_k.shape)
    return leaf, ramp, dct_mask, internal, sizes, offs, int(flat.sum())


def _gather(data: np.ndarray, offs: np.ndarray, mask: np.ndarray, nbytes: int) -> np.ndarray:
    """Lê nbytes a partir de cada offset dos nós em mask (ordem row-major)."""
    o = offs[mask]
    return data[o[:, None] + np.arange(nbytes)]


def _paint_ramps(
    canvas: np.ndarray, ramp_mask: np.ndarray, corner_bytes: np.ndarray, s: int,
    row_off: int = 0, col_off: int = 0,
) -> None:
    """Pinta blocos rampa no canvas (visto como grade de blocos s×s)."""
    ci, cj = np.nonzero(ramp_mask)
    if len(ci) == 0:
        return
    rec = ramp_reconstruct(corner_bytes.reshape(-1, 4, 3), s)
    gh = canvas.shape[0] // s
    gw = canvas.shape[1] // s
    c4 = canvas.reshape(gh, s, gw, s, 3)
    sy = np.arange(s)
    c4[
        (ci - row_off)[:, None, None], sy[None, :, None],
        (cj - col_off)[:, None, None], sy[None, None, :],
    ] = rec


def _paint_dct(
    canvas: np.ndarray, dct_mask: np.ndarray, coeff_bytes: np.ndarray, s: int,
    row_off: int = 0, col_off: int = 0,
) -> None:
    """Pinta blocos DCT no canvas (visto como grade de blocos sÃ—s)."""
    ci, cj = np.nonzero(dct_mask)
    if len(ci) == 0:
        return
    coeff = (
        coeff_bytes.reshape(-1, dct.PAYLOAD_BYTES)
        .view("<i2")
        .reshape(-1, dct.COEFF_N, dct.COEFF_N, 3)
    )
    rec = dct.reconstruct(coeff, s)
    gh = canvas.shape[0] // s
    gw = canvas.shape[1] // s
    c4 = canvas.reshape(gh, s, gw, s, 3)
    sy = np.arange(s)
    c4[
        (ci - row_off)[:, None, None], sy[None, :, None],
        (cj - col_off)[:, None, None], sy[None, None, :],
    ] = rec


def _parse_level(blob, header, table, offset, k, types_prev):
    struct_size, data_size = table[k]
    struct_bytes = blob[offset : offset + struct_size]
    data = np.frombuffer(blob, dtype=np.uint8, count=data_size,
                         offset=offset + struct_size)
    if k == 0:
        types_k = np.array([[header.root_type]], dtype=np.uint8)
    else:
        types_k = _unpack_children(struct_bytes, types_prev == INTERNAL, header.wide_types)
    return types_k, data, offset + struct_size + data_size


def decode_full(blob: bytes) -> tuple[np.ndarray, dict]:
    """Decodifica o arquivo inteiro. Retorna (imagem H×W×3 uint8, info)."""
    header = Header.unpack(blob)
    levels = header.levels
    table = unpack_level_table(blob, HEADER_SIZE, levels)
    offset = HEADER_SIZE + level_table_size(levels)

    size = 2**levels
    out = np.zeros((size, size, 3), dtype=np.uint8)
    types_prev: np.ndarray | None = None
    nodes_visited = 0

    for k in range(levels + 1):
        types_k, data, offset = _parse_level(blob, header, table, offset, k, types_prev)
        leaf, ramp, dct_mask, internal, sizes, offs, total = _payload_layout(types_k, header.pyramid)
        if len(data) != total:
            raise ValueError(f"payload corrompido no nível {k}")
        nodes_visited += int((types_k != NOT_MAT).sum())

        gk = 2**k
        s = size // gk
        if leaf.any():
            vals = np.zeros((gk, gk, 3), dtype=np.uint8)
            vals[leaf] = _gather(data, offs, leaf, 3)
            up_mask = np.repeat(np.repeat(leaf, s, axis=0), s, axis=1)
            up_vals = np.repeat(np.repeat(vals, s, axis=0), s, axis=1)
            out[up_mask] = up_vals[up_mask]
        if ramp.any():
            _paint_ramps(out, ramp, _gather(data, offs, ramp, 12), s)
        if dct_mask.any():
            _paint_dct(out, dct_mask, _gather(data, offs, dct_mask, dct.PAYLOAD_BYTES), s)

        types_prev = types_k

    info = {
        "bytes_read": len(blob),
        "nodes_visited": nodes_visited,
        "levels": levels,
        "lossy": header.lossy,
        "pyramid": header.pyramid,
    }
    return out[: header.height, : header.width], info


def decode_progressive(blob: bytes, max_level: int) -> tuple[np.ndarray, dict]:
    """Lê o stream até o nível `max_level` e PARA — alegação C1."""
    header = Header.unpack(blob)
    levels = header.levels
    max_level = min(max_level, levels)
    if not header.pyramid and max_level < levels:
        raise ValueError(
            "decode progressivo parcial requer pirâmide de médias "
            "(arquivo codificado com pyramid=False)"
        )
    table = unpack_level_table(blob, HEADER_SIZE, levels)
    offset = HEADER_SIZE + level_table_size(levels)
    bytes_read = offset

    size = 2**levels
    out = np.zeros((size, size, 3), dtype=np.uint8)
    types_prev: np.ndarray | None = None

    for k in range(max_level + 1):
        struct_size, data_size = table[k]
        types_k, data, offset = _parse_level(blob, header, table, offset, k, types_prev)
        bytes_read += struct_size + data_size
        leaf, ramp, dct_mask, internal, sizes, offs, total = _payload_layout(types_k, header.pyramid)
        if len(data) != total:
            raise ValueError(f"payload corrompido no nível {k}")

        gk = 2**k
        s = size // gk
        # no nível de corte, ramos abertos pintam a média da pirâmide
        const_paint = leaf | internal if k == max_level else leaf
        if const_paint.any():
            vals = np.zeros((gk, gk, 3), dtype=np.uint8)
            if leaf.any():
                vals[leaf] = _gather(data, offs, leaf, 3)
            if k == max_level and internal.any():
                vals[internal] = _gather(data, offs, internal, 3)
            up_mask = np.repeat(np.repeat(const_paint, s, axis=0), s, axis=1)
            up_vals = np.repeat(np.repeat(vals, s, axis=0), s, axis=1)
            out[up_mask] = up_vals[up_mask]
        if ramp.any():
            _paint_ramps(out, ramp, _gather(data, offs, ramp, 12), s)
        if dct_mask.any():
            _paint_dct(out, dct_mask, _gather(data, offs, dct_mask, dct.PAYLOAD_BYTES), s)

        types_prev = types_k

    info = {
        "bytes_read": bytes_read,
        "total_bytes": len(blob),
        "fraction": bytes_read / len(blob),
        "level": max_level,
        "levels": levels,
        "preview_grid": 2**max_level,
    }
    return out[: header.height, : header.width], info


def decode_roi(blob: bytes, x: int, y: int, w: int, h: int) -> tuple[np.ndarray, dict]:
    """Decodifica só a região (x, y, w, h) — alegação C2.

    Lê TODA a estrutura (barata) e faz seek apenas nos payloads das
    folhas (constantes ou rampas) que intersectam a região.
    """
    header = Header.unpack(blob)
    levels = header.levels
    if not (0 <= x and 0 <= y and w > 0 and h > 0
            and x + w <= header.width and y + h <= header.height):
        raise ValueError("ROI fora dos limites da imagem")
    table = unpack_level_table(blob, HEADER_SIZE, levels)
    offset = HEADER_SIZE + level_table_size(levels)

    size = 2**levels
    out = np.zeros((h, w, 3), dtype=np.uint8)
    types_prev: np.ndarray | None = None
    struct_bytes_read = HEADER_SIZE + level_table_size(levels)
    payload_bytes_read = 0
    total_payload = 0
    seeks = 0

    for k in range(levels + 1):
        struct_size, data_size = table[k]
        types_k, data, offset = _parse_level(blob, header, table, offset, k, types_prev)
        types_prev = types_k
        struct_bytes_read += struct_size
        total_payload += data_size
        leaf, ramp, dct_mask, internal, sizes, offs, total = _payload_layout(types_k, header.pyramid)
        if len(data) != total:
            raise ValueError(f"payload corrompido no nível {k}")

        s = size >> k
        i0, i1 = y // s, (y + h - 1) // s + 1
        j0, j1 = x // s, (x + w - 1) // s + 1
        block = np.zeros_like(leaf)
        block[i0:i1, j0:j1] = True
        need_leaf = leaf & block
        need_ramp = ramp & block
        need_dct = dct_mask & block
        if not (need_leaf.any() or need_ramp.any() or need_dct.any()):
            continue

        # contabilidade de leitura: offsets/tamanhos dos nós necessários
        all_offs = np.concatenate([offs[need_leaf], offs[need_ramp], offs[need_dct]])
        all_sizes = np.concatenate([
            np.full(int(need_leaf.sum()), 3, np.int64),
            np.full(int(need_ramp.sum()), 12, np.int64),
            np.full(int(need_dct.sum()), dct.PAYLOAD_BYTES, np.int64),
        ])
        order = np.argsort(all_offs)
        so, ss = all_offs[order], all_sizes[order]
        payload_bytes_read += int(ss.sum())
        seeks += 1 + int(np.count_nonzero(so[1:] != so[:-1] + ss[:-1]))

        # canvas do bloco de nós que cobre a ROI neste nível
        bh_, bw_ = (i1 - i0) * s, (j1 - j0) * s
        canvas = np.zeros((bh_, bw_, 3), dtype=np.uint8)
        painted = np.zeros((bh_, bw_), dtype=bool)
        if need_leaf.any():
            sub_mask = need_leaf[i0:i1, j0:j1]
            sub_vals = np.zeros((i1 - i0, j1 - j0, 3), dtype=np.uint8)
            sub_vals[sub_mask] = _gather(data, offs, need_leaf, 3)
            um = np.repeat(np.repeat(sub_mask, s, axis=0), s, axis=1)
            canvas[um] = np.repeat(np.repeat(sub_vals, s, axis=0), s, axis=1)[um]
            painted |= um
        if need_ramp.any():
            _paint_ramps(canvas, need_ramp[i0:i1, j0:j1],
                         _gather(data, offs, need_ramp, 12), s)
            painted |= np.repeat(np.repeat(need_ramp[i0:i1, j0:j1], s, axis=0),
                                 s, axis=1)
        if need_dct.any():
            _paint_dct(canvas, need_dct[i0:i1, j0:j1],
                       _gather(data, offs, need_dct, dct.PAYLOAD_BYTES), s)
            painted |= np.repeat(np.repeat(need_dct[i0:i1, j0:j1], s, axis=0),
                                 s, axis=1)

        ry, rx = y - i0 * s, x - j0 * s
        pm = painted[ry : ry + h, rx : rx + w]
        out[pm] = canvas[ry : ry + h, rx : rx + w][pm]

    bytes_read = struct_bytes_read + payload_bytes_read
    info = {
        "bytes_read": bytes_read,
        "struct_bytes_read": struct_bytes_read,
        "payload_bytes_read": payload_bytes_read,
        "total_payload_bytes": total_payload,
        "total_bytes": len(blob),
        "fraction": bytes_read / len(blob),
        "payload_fraction": (payload_bytes_read / total_payload) if total_payload else 0.0,
        "seeks": seeks,
        "roi": (x, y, w, h),
        "roi_area_fraction": (w * h) / (header.width * header.height),
    }
    return out, info
