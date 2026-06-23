"""Wafer quadtree — K camadas co-registradas sobre UMA hierarquia.

Subdivisão-UNIÃO: um nó é folha sse TODAS as camadas são homogêneas nele.
A estrutura (subdivisão) é partilhada; cada folha guarda K payloads.

Contabilidade honesta: estrutura (bytes da subdivisão, partilhada) vs
payload (bytes por camada, cobrados por Shannon). Comparado contra o
baseline: cada camada com sua própria quadtree (estrutura replicada).

Lossless: folha sse o bloco é constante (por canal) em cada camada — o
payload por camada/folha é o valor constante (channels bytes).
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import numpy as np

STRUCT_BYTE_PER_INTERNAL = 1  # 4 filhos × 2 bits = 1 byte por nó interno


def _homog(block: np.ndarray, t: float) -> bool:
    """True se o bloco é homogêneo (max-min ≤ t por canal)."""
    flat = block.reshape(-1, block.shape[-1])
    return bool((flat.max(0) - flat.min(0) <= t).all())


@dataclass
class TreeCost:
    internal: int
    leaves: int

    @property
    def struct_bytes(self) -> int:
        return self.internal * STRUCT_BYTE_PER_INTERNAL


def _build_union(layers: list[np.ndarray], y: int, x: int, s: int, t: float) -> TreeCost:
    """Quadtree união sobre todas as camadas. Conta nós internos/folhas."""
    if s == 1 or all(_homog(L[y:y + s, x:x + s], t) for L in layers):
        return TreeCost(0, 1)
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        c = _build_union(layers, y + dy, x + dx, h, t)
        ni += c.internal
        nl += c.leaves
    return TreeCost(ni + 1, nl)


def _build_single(layer: np.ndarray, y: int, x: int, s: int, t: float) -> TreeCost:
    if s == 1 or _homog(layer[y:y + s, x:x + s], t):
        return TreeCost(0, 1)
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        c = _build_single(layer, y + dy, x + dx, h, t)
        ni += c.internal
        nl += c.leaves
    return TreeCost(ni + 1, nl)


def _walk_base(layer: np.ndarray, y: int, x: int, s: int, t: float, leaves: list[tuple[int, int, int]]) -> TreeCost:
    """Build base tree and collect its leaves as (y, x, size)."""
    if s == 1 or _homog(layer[y:y + s, x:x + s], t):
        leaves.append((y, x, s))
        return TreeCost(0, 1)
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        c = _walk_base(layer, y + dy, x + dx, h, t, leaves)
        ni += c.internal
        nl += c.leaves
    return TreeCost(ni + 1, nl)


def _derive_luminance(rgb: np.ndarray) -> np.ndarray:
    lum = np.rint(rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float64)).astype(np.uint8)
    return lum[:, :, None]


def _reconstruct_refined_layer(
    layer: np.ndarray,
    leaves: list[tuple[int, int, int]],
    threshold: float,
) -> np.ndarray:
    """ReconstrÃ³i uma camada usando a partiÃ§Ã£o base e refinamentos locais."""
    out = np.zeros_like(layer)

    def fill(y: int, x: int, sz: int) -> None:
        if sz == 1 or _homog(layer[y:y + sz, x:x + sz], threshold):
            block = layer[y:y + sz, x:x + sz]
            out[y:y + sz, x:x + sz] = block[0, 0] if threshold == 0 else np.rint(block.mean(0)).astype(layer.dtype)
            return
        h = sz // 2
        for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
            fill(y + dy, x + dx, h)

    for y, x, sz in leaves:
        fill(y, x, sz)
    return out


def _channels(layer: np.ndarray) -> int:
    return layer.shape[-1]


def measure(layers: list[np.ndarray], threshold: float = 0.0) -> dict:
    """Mede wafer (estrutura partilhada) vs independente (K árvores).

    Todas as camadas devem ser H×W×C, H==W potência de 2, co-dimensionadas.
    """
    s = layers[0].shape[0]
    assert all(L.shape[0] == s and L.shape[1] == s for L in layers), "co-registrar dims"
    assert (s & (s - 1)) == 0, "lado deve ser potência de 2"

    union = _build_union(layers, 0, 0, s, threshold)
    chan_sum = sum(_channels(L) for L in layers)
    wafer_struct = union.struct_bytes
    wafer_payload = union.leaves * chan_sum
    wafer_total = wafer_struct + wafer_payload

    indep_struct = 0
    indep_payload = 0
    per_layer = []
    for L in layers:
        c = _build_single(L, 0, 0, s, threshold)
        st = c.struct_bytes
        pl = c.leaves * _channels(L)
        indep_struct += st
        indep_payload += pl
        per_layer.append({"internal": c.internal, "leaves": c.leaves,
                          "struct": st, "payload": pl})
    indep_total = indep_struct + indep_payload

    return {
        "side": s,
        "n_layers": len(layers),
        "wafer": {"struct": wafer_struct, "payload": wafer_payload,
                  "total": wafer_total, "internal": union.internal,
                  "leaves": union.leaves},
        "indep": {"struct": indep_struct, "payload": indep_payload,
                  "total": indep_total, "per_layer": per_layer},
        "ratio": indep_total / wafer_total if wafer_total else float("inf"),
        "struct_saved": indep_struct - wafer_struct,
        "payload_overhead": wafer_payload - indep_payload,
    }


def measure_with_derived(
    layers: list[np.ndarray],
    derived: set[int],
    threshold: float = 0.0,
) -> dict:
    """Mede wafer quando algumas camadas sao derivadas de outras.

    A estrutura continua sendo a uniao das K camadas, mas as camadas em
    `derived` nao pagam payload: elas sao recuperadas por uma regra externa
    deterministica (ex.: luminancia derivada de RGB). Isso mede informacao
    mutua/correlacao entre camadas, sem dizer que payload independente e gratis.
    """
    m = measure(layers, threshold=threshold)
    derived_channels = sum(_channels(layers[i]) for i in derived)
    saved = m["wafer"]["leaves"] * derived_channels
    m = {
        **m,
        "derived_layers": sorted(derived),
        "derived_payload_saved": saved,
    }
    m["wafer"] = {
        **m["wafer"],
        "payload_raw": m["wafer"]["payload"],
        "payload": m["wafer"]["payload"] - saved,
    }
    m["wafer"]["total"] = m["wafer"]["struct"] + m["wafer"]["payload"]
    m["ratio"] = m["indep"]["total"] / m["wafer"]["total"] if m["wafer"]["total"] else float("inf")
    m["payload_overhead"] = m["wafer"]["payload"] - m["indep"]["payload"]
    return m


def measure_with_refinements(
    layers: list[np.ndarray],
    base_layer: int = 0,
    derived: set[int] | None = None,
    threshold: float = 0.0,
) -> dict:
    """Mede wafer com arvore base + refinamentos locais por camada.

    Diferente da uniao rigida, uma camada que precisa de mais detalhe paga
    uma mini-quadtree local apenas dentro da folha base. As outras camadas nao
    sao arrastadas para essa subdivisao.
    """
    derived = set() if derived is None else set(derived)
    s = layers[0].shape[0]
    assert all(L.shape[0] == s and L.shape[1] == s for L in layers), "co-registrar dims"
    assert (s & (s - 1)) == 0, "lado deve ser potencia de 2"

    leaves: list[tuple[int, int, int]] = []
    base = _walk_base(layers[base_layer], 0, 0, s, threshold, leaves)
    base_struct = base.struct_bytes
    base_payload = base.leaves * _channels(layers[base_layer])

    refine_struct = 0
    refine_payload = 0
    per_extra = []
    for i, L in enumerate(layers):
        if i == base_layer or i in derived:
            per_extra.append({"layer": i, "derived": i in derived, "struct": 0, "payload": 0})
            continue
        st = 0
        pl = 0
        for y, x, sz in leaves:
            if _homog(L[y:y + sz, x:x + sz], threshold):
                pl += _channels(L)
            else:
                c = _build_single(L, y, x, sz, threshold)
                st += c.struct_bytes
                pl += c.leaves * _channels(L)
        refine_struct += st
        refine_payload += pl
        per_extra.append({"layer": i, "derived": False, "struct": st, "payload": pl})

    indep_struct = 0
    indep_payload = 0
    per_layer = []
    for L in layers:
        c = _build_single(L, 0, 0, s, threshold)
        st = c.struct_bytes
        pl = c.leaves * _channels(L)
        indep_struct += st
        indep_payload += pl
        per_layer.append({"internal": c.internal, "leaves": c.leaves,
                          "struct": st, "payload": pl})

    wafer_struct = base_struct + refine_struct
    wafer_payload = base_payload + refine_payload
    wafer_total = wafer_struct + wafer_payload
    indep_total = indep_struct + indep_payload
    return {
        "side": s,
        "n_layers": len(layers),
        "base_layer": base_layer,
        "derived_layers": sorted(derived),
        "wafer": {"struct": wafer_struct, "payload": wafer_payload,
                  "total": wafer_total, "base_struct": base_struct,
                  "refine_struct": refine_struct, "base_leaves": base.leaves},
        "indep": {"struct": indep_struct, "payload": indep_payload,
                  "total": indep_total, "per_layer": per_layer},
        "ratio": indep_total / wafer_total if wafer_total else float("inf"),
        "struct_saved": indep_struct - wafer_struct,
        "payload_overhead": wafer_payload - indep_payload,
        "per_extra": per_extra,
    }


def reconstruct_with_refinements(
    layers: list[np.ndarray],
    base_layer: int = 0,
    derived_rules: dict[int, Callable[[np.ndarray], np.ndarray]] | None = None,
    threshold: float = 0.0,
) -> list[np.ndarray]:
    """ReconstrÃ³i cada camada usando a base partilhada + refinamentos locais.

    `derived_rules` mapeia Ã­ndices de camadas derivadas para funÃ§Ãµes
    determinÃ­sticas que recebem a camada-base e devolvem a camada derivada.
    """
    derived_rules = {} if derived_rules is None else dict(derived_rules)
    s = layers[0].shape[0]
    leaves: list[tuple[int, int, int]] = []
    _walk_base(layers[base_layer], 0, 0, s, threshold, leaves)

    recon: list[np.ndarray] = [None] * len(layers)  # type: ignore[list-item]
    base_recon = _reconstruct_refined_layer(layers[base_layer], leaves, threshold)
    recon[base_layer] = base_recon
    for i, L in enumerate(layers):
        if i == base_layer:
            continue
        if i in derived_rules:
            recon[i] = derived_rules[i](base_recon)
            continue
        recon[i] = _reconstruct_refined_layer(L, leaves, threshold)
    return recon


def reconstruct_layer(layers: list[np.ndarray], li: int, threshold: float = 0.0) -> np.ndarray:
    """Reconstrói a camada `li` a partir do wafer (folhas união → valor médio).

    Serve ao gate de correção: lossless (threshold 0) deve bater o original.
    """
    s = layers[0].shape[0]
    L = layers[li]
    out = np.zeros_like(L)

    def rec(y, x, sz):
        if sz == 1 or all(_homog(M[y:y + sz, x:x + sz], threshold) for M in layers):
            block = L[y:y + sz, x:x + sz].reshape(-1, L.shape[-1])
            val = block[0] if threshold == 0 else np.rint(block.mean(0)).astype(L.dtype)
            out[y:y + sz, x:x + sz] = val
            return
        h = sz // 2
        for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
            rec(y + dy, x + dx, h)

    rec(0, 0, s)
    return out
