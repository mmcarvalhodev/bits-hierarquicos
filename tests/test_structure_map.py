"""Terceira leitura — mapa de complexidade lido só da estrutura."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bench import corpus  # noqa: E402
from bhc import encode  # noqa: E402
from bhc.structure_map import decode_structure_map  # noqa: E402


def test_structure_map_distinguishes_detail_from_smooth():
    """Metade lisa, metade ruidosa: o mapa deve separar as duas SEM
    ler um único byte de payload."""
    img = corpus.flat(256, 256, (120, 120, 120))
    img[:, 128:] = corpus.noise(128, 256, seed=3)
    blob, _ = encode(img, pyramid=True)
    smap, info = decode_structure_map(blob)
    g = smap.shape[1]
    left = smap[:, : g // 2].mean()
    right = smap[:, g // 2 :].mean()
    assert right > left + 50, f"mapa não separa liso de detalhado: {left} vs {right}"


def test_structure_map_reads_fraction_of_file():
    img = corpus.noise(512, 512)
    blob, _ = encode(img, pyramid=True)
    _, info = decode_structure_map(blob)
    assert info["fraction"] < 0.10, f"estrutura cara demais: {info['fraction']:.2%}"


def test_structure_map_flat_is_zero():
    blob, _ = encode(corpus.flat(128, 128))
    smap, info = decode_structure_map(blob)
    assert smap.max() == 0  # raiz já é folha: nenhuma subdivisão
