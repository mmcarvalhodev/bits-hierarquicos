"""Terceira leitura do stream: mapa de complexidade SEM payload.

Demonstração da tese "hierarquia é interpretação": os bytes de ESTRUTURA
do arquivo (1 byte por nó interno, ~1-8% do total) nunca foram escritos
como "mapa de detalhe" — mas lidos sob outra convenção, são exatamente
isso. Onde a árvore subdivide fundo há detalhe/borda; onde termina cedo
há lisura. Nenhum payload é tocado.

Saída: grade (res × res) uint8 onde o valor é a profundidade em que o
ramo terminou (normalizada 0-255) — um mapa de saliência/complexidade
que custa a leitura da estrutura, não do arquivo.
"""
from __future__ import annotations

import numpy as np

from .format import (
    HEADER_SIZE, INTERNAL, Header, level_table_size, unpack_level_table,
)
from .decoder import _unpack_children


def decode_structure_map(blob: bytes, max_level: int | None = None) -> tuple[np.ndarray, dict]:
    """Lê SÓ as seções de estrutura e devolve o mapa de profundidade.

    Retorna (mapa H×W uint8 em resolução reduzida, info com bytes lidos).
    """
    header = Header.unpack(blob)
    levels = header.levels
    k_max = levels if max_level is None else min(max_level, levels)
    table = unpack_level_table(blob, HEADER_SIZE, levels)
    offset = HEADER_SIZE + level_table_size(levels)
    bytes_read = offset

    size = 2**levels
    depth = np.zeros((1, 1), dtype=np.uint8)  # profundidade de término por ramo
    types_prev = np.array([[header.root_type]], dtype=np.uint8)

    for k in range(1, k_max + 1):
        struct_size, data_size = table[k - 1]
        offset += struct_size + data_size  # pula payload do nível anterior
        struct_size, _ = table[k]
        struct_bytes = blob[offset : offset + struct_size]
        bytes_read += struct_size  # payload NUNCA é lido

        types_k = _unpack_children(struct_bytes, types_prev == INTERNAL, header.wide_types)
        # ramos que continuam ganham profundidade; terminados congelam
        depth = np.repeat(np.repeat(depth, 2, axis=0), 2, axis=1)
        depth[types_k == INTERNAL] = k
        types_prev = types_k

    # normaliza para 0-255 e recorta a região real
    if k_max > 0:
        depth = (depth.astype(np.float64) * (255.0 / k_max)).astype(np.uint8)
    g = depth.shape[0]
    scale = size // g
    hh = -(-header.height // scale)
    ww = -(-header.width // scale)
    info = {
        "bytes_read": bytes_read,
        "total_bytes": len(blob),
        "fraction": bytes_read / len(blob),
        "grid": g,
        "level": k_max,
    }
    return depth[:hh, :ww], info
