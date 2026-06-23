"""Fatia 1 — STORAGE: substrato BH unificado vs pilha costurada (4 peças).

Ativo multimodal co-registrado (RGB + depth + seg + embeddings por região).
Compara o storage total das 4 peças SOTA costuradas contra UMA hierarquia BH.
Critério declarado na spec: vence se storage_unificado <= storage_costurado.

Honestidade: mede storage (a fatia mais decisiva e barata). Acesso e temporal
são fatias 2-3. Embeddings dominam o custo (Shannon: pagos pelos dois lados);
o diferencial é estrutura partilhada + índice/rendition que somem no unificado.
"""
from __future__ import annotations

import numpy as np

SIDE = 256
STRUCT_BYTE = 1          # 1 byte por nó interno (4 filhos × 2 bits)
M_HNSW = 16              # conexões/nó do grafo HNSW (modelo publicado)
HNSW_BYTES = M_HNSW * 8  # overhead do grafo por vetor


def _homog(block, t=0.0):
    f = block.reshape(-1, block.shape[-1])
    return bool((f.max(0) - f.min(0) <= t).all())


def _count(layer, y, x, s):
    """quadtree de uma camada: (internos, folhas)."""
    if s == 1 or _homog(layer[y:y + s, x:x + s]):
        return 0, 1
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        a, b = _count(layer, y + dy, x + dx, h)
        ni += a; nl += b
    return ni + 1, nl


def _count_union(layers, y, x, s):
    if s == 1 or all(_homog(L[y:y + s, x:x + s]) for L in layers):
        return 0, 1
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        a, b = _count_union(layers, y + dy, x + dx, h)
        ni += a; nl += b
    return ni + 1, nl


def make_partition(side, seed, p=0.72, minb=4):
    rng = np.random.default_rng(seed)
    region = np.zeros((side, side), dtype=np.int32)
    nid = [0]

    def rec(y, x, s):
        if s <= minb or rng.random() > p:
            region[y:y + s, x:x + s] = nid[0]; nid[0] += 1; return
        h = s // 2
        for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
            rec(y + dy, x + dx, h)
    rec(0, 0, side)
    return region, nid[0]


def layer_from(region, ch, seed):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (region.max() + 1, ch), dtype=np.uint8)[region]


def fmt(b):
    if b >= 1e6: return f"{b/1e6:.2f} MB"
    if b >= 1e3: return f"{b/1e3:.1f} KB"
    return f"{b:.0f} B"


def run(d_emb: int):
    # ativo co-registrado: RGB + depth + seg sobre a MESMA partição
    region, n_reg = make_partition(SIDE, seed=1)
    rgb = layer_from(region, 3, 10)
    depth = layer_from(region, 1, 11)
    seg = layer_from(region, 1, 12)
    layers = [rgb, depth, seg]

    # custos por camada (independente) e união
    ni_rgb, nl_rgb = _count(rgb, 0, 0, SIDE)
    ni_dep, nl_dep = _count(depth, 0, 0, SIDE)
    ni_seg, nl_seg = _count(seg, 0, 0, SIDE)
    ni_u, nl_u = _count_union(layers, 0, 0, SIDE)
    n_emb = nl_u  # 1 embedding por região-folha

    # ---------- PILHA COSTURADA (4 peças) ----------
    s_struct = (ni_rgb + ni_dep + ni_seg) * STRUCT_BYTE          # 1. storage: 3 estruturas
    s_payload = nl_rgb * 3 + nl_dep * 1 + nl_seg * 1             #    + payloads
    s_emb_vec = n_emb * d_emb * 4                                #    + vetores embeddings
    s_hnsw = n_emb * HNSW_BYTES                                  # 2. índice vetorial (grafo)
    s_thumb = (SIDE // 8) ** 2 * 3                               # 3. rendition (preview)
    s_spatial = n_emb * 20                                       # 4. índice espacial (bbox+id)
    stitched = s_struct + s_payload + s_emb_vec + s_hnsw + s_thumb + s_spatial

    # ---------- SUBSTRATO BH UNIFICADO ----------
    u_struct = ni_u * STRUCT_BYTE                                # estrutura partilhada (1×)
    u_payload = nl_u * (3 + 1 + 1)                               # RGB+depth+seg por folha
    u_emb_vec = n_emb * d_emb * 4                                # embeddings folha (Shannon)
    u_emb_summary = ni_u * d_emb * 4                             # resumo de embedding no nó (p/ Q3)
    # preview FREE (lê o topo) → sem thumbnail; índice espacial FREE (a hierarquia É o índice)
    unified = u_struct + u_payload + u_emb_vec + u_emb_summary

    return {
        "d": d_emb, "n_emb": n_emb,
        "stitched": {
            "struct(3×)": s_struct, "payload": s_payload, "embeddings": s_emb_vec,
            "HNSW": s_hnsw, "thumbnail": s_thumb, "spatial_idx": s_spatial,
            "total": stitched,
        },
        "unified": {
            "struct(1×)": u_struct, "payload": u_payload, "embeddings": u_emb_vec,
            "emb_summary": u_emb_summary, "thumbnail": 0, "spatial_idx": 0,
            "total": unified,
        },
        "ratio": stitched / unified,
    }


def main():
    L = ["# MULTIMODAL — FATIA 1 (STORAGE): substrato unificado vs pilha costurada\n"]
    L.append(f"Ativo co-registrado {SIDE}×{SIDE} (RGB+depth+seg+embeddings por região). "
             "Pilha costurada = storage(3 arquivos) + HNSW + thumbnail + índice espacial. "
             "Unificado = 1 hierarquia (preview e índice espacial FREE).\n")
    L.append("Varre d (dim do embedding): d pequeno → estrutura/índice pesam → "
             "unificado ganha mais; d grande → embeddings dominam (Shannon) → empata.\n")
    L.append("| d (emb) | nº regiões | costurado | unificado | ganho |")
    L.append("|---|---|---|---|---|")
    rows = [run(d) for d in (8, 32, 64, 128, 256)]
    for r in rows:
        L.append(f"| {r['d']} | {r['n_emb']:,} | {fmt(r['stitched']['total'])} | "
                 f"{fmt(r['unified']['total'])} | **{r['ratio']:.2f}×** |")

    # breakdown no caso d=64
    r = next(x for x in rows if x["d"] == 64)
    L.append("\n## Breakdown (d=64) — onde o unificado economiza\n")
    L.append("| componente | costurado | unificado |")
    L.append("|---|---|---|")
    for k in ["struct(3×)", "payload", "embeddings", "HNSW", "thumbnail", "spatial_idx"]:
        sv = r["stitched"].get(k, 0)
        uk = {"struct(3×)": "struct(1×)", "HNSW": "emb_summary"}.get(k, k)
        uv = r["unified"].get(uk, r["unified"].get(k, 0))
        L.append(f"| {k} → {uk} | {fmt(sv)} | {fmt(uv)} |")

    L.append("\n## LEITURA HONESTA\n")
    big_d = next(x for x in rows if x["d"] == 256)["ratio"]
    small_d = next(x for x in rows if x["d"] == 8)["ratio"]
    L.append(f"- **O ganho depende de quanto os embeddings dominam.** d pequeno: "
             f"{small_d:.2f}× (estrutura+índice+rendition pesam, unificado ganha). "
             f"d grande: {big_d:.2f}× (embeddings dominam — Shannon paga igual dos dois "
             f"lados — o ganho encolhe). É a mesma lição do wafer: payload domina → "
             f"estrutura partilhada rende pouco.")
    L.append("- **SINAL NEGATIVO p/ produto-de-storage:** o cruzamento é em d≈96-128, "
             "mas embeddings de IA modernos são d=768–4096. Nesse regime real, o "
             "unificado PERDE em storage — porque o resumo-de-embedding no nó custa "
             "O(n_internos × d), que cresce com d, enquanto o grafo HNSW é O(n × M), "
             "constante em d. Storage NÃO é o ângulo de produto em embeddings reais.")
    L.append("- **Ressalva:** o índice unificado aqui é ingênuo (centroide d-dim em todo "
             "nó interno). Um resumo projetado/baixa-dim para poda poderia recuperar — "
             "mas é não-medido. Não vendas storage; o ângulo, se existir, é acesso+ops.")
    L.append("- **O que o unificado elimina de verdade:** as 3 estruturas viram 1; o "
             "thumbnail (rendition) some (preview é free); o índice espacial some (a "
             "hierarquia É o índice). O HNSW vira resumo-de-embedding no nó.")
    L.append("- **A fronteira:** se a carga for retrieval GLOBAL (não escopado), o HNSW "
             "volta a ser preciso e o unificado não o substitui. E conteúdo "
             "não-co-registrado faria a união super-subdividir (fronteira W3).")
    L.append("- **Fatia 1 mede STORAGE.** O valor de produto real inclui acesso (fatia "
             "2), temporal/vídeo (fatia 3) e $ de operação (fatia 4) — e a simplicidade "
             "de 1 sistema vs 4, que não cabe num número mas é metade do argumento.")

    out = __import__("pathlib").Path(__file__).resolve().parents[1] / "RESULTS_FATIA1_STORAGE.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    for r in rows:
        print(f"d={r['d']:3d}  costurado={fmt(r['stitched']['total']):>10}  "
              f"unificado={fmt(r['unified']['total']):>10}  ganho={r['ratio']:.2f}×")
    print(f"\nrelatório: {out}")


if __name__ == "__main__":
    main()
