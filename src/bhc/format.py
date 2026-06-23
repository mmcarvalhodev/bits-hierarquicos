"""BHC v0 — constantes e cabeçalho do formato.

Layout do arquivo (little-endian):
    [MAGIC "BHC0" 4B]
    [GLOBAL HEADER 20B]  width u32 | height u32 | levels u8 | mode u8 |
                         colorspace u8 | threshold f32 | root_type u8
    [LEVEL TABLE]        (levels+1) × (struct_size u32 | data_size u32)
    [LEVEL 0..N]         por nível: [STRUCTURE][DATA]

A posição de cada nó é IMPLÍCITA na ordenação BFS/row-major do stream —
o campo HIERARCHY do documento conceitual não é armazenado (ver spec §3.4).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

MAGIC = b"BHC0"

# Tipos de nó (2 bits no byte de estrutura) — o selector de INTERPRETAÇÃO:
# cada nó declara como seu payload deve ser lido (v0.2, multi-interpretação)
LEAF = 0           # constante: payload 3B (cor única)
INTERNAL = 1       # subdivide: payload 3B (média) se pirâmide, senão 0
EMPTY = 2          # quadrante totalmente fora da imagem real (padding)
RAMP = 3           # rampa bilinear: payload 12B (4 cantos RGB)
DCT = 4            # mini-DCT low-frequency: payload 4x4x3 int16
NOT_MAT = 255      # não materializado (pai não é INTERNAL) — nunca no arquivo

# Bits do campo mode
MODE_LOSSY = 0x01
MODE_PYRAMID = 0x02
MODE_WIDE_TYPES = 0x04

COLORSPACE_RGB = 1

_HEADER_FMT = "<IIBBBfB"  # width, height, levels, mode, colorspace, threshold, root_type
HEADER_SIZE = len(MAGIC) + struct.calcsize(_HEADER_FMT)


@dataclass(frozen=True)
class Header:
    width: int
    height: int
    levels: int          # N — nível folha; grade do nível k tem 2^k × 2^k nós
    lossy: bool
    pyramid: bool
    wide_types: bool
    threshold: float
    root_type: int

    @property
    def mode(self) -> int:
        return (
            (MODE_LOSSY if self.lossy else 0)
            | (MODE_PYRAMID if self.pyramid else 0)
            | (MODE_WIDE_TYPES if self.wide_types else 0)
        )

    def pack(self) -> bytes:
        return MAGIC + struct.pack(
            _HEADER_FMT, self.width, self.height, self.levels,
            self.mode, COLORSPACE_RGB, self.threshold, self.root_type,
        )

    @classmethod
    def unpack(cls, buf: bytes) -> "Header":
        if buf[: len(MAGIC)] != MAGIC:
            raise ValueError("não é um arquivo BHC (magic inválido)")
        width, height, levels, mode, colorspace, threshold, root_type = struct.unpack_from(
            _HEADER_FMT, buf, len(MAGIC)
        )
        if colorspace != COLORSPACE_RGB:
            raise ValueError(f"colorspace não suportado: {colorspace}")
        return cls(
            width=width, height=height, levels=levels,
            lossy=bool(mode & MODE_LOSSY), pyramid=bool(mode & MODE_PYRAMID),
            wide_types=bool(mode & MODE_WIDE_TYPES),
            threshold=threshold, root_type=root_type,
        )


def pack_level_table(entries: list[tuple[int, int]]) -> bytes:
    return b"".join(struct.pack("<II", s, d) for s, d in entries)


def unpack_level_table(buf: bytes, offset: int, levels: int) -> list[tuple[int, int]]:
    entries = []
    for i in range(levels + 1):
        s, d = struct.unpack_from("<II", buf, offset + 8 * i)
        entries.append((s, d))
    return entries


def level_table_size(levels: int) -> int:
    return 8 * (levels + 1)
