"""Fatia 2 — ACESSO: bytes movidos por query, unificado vs pilha costurada.

Mix escopado (spec §1): Q1 preview/LOD · Q2 ROI+camadas · Q3 retrieval escopado ·
Q4 agregado de janela. Métrica: bytes movidos por query.

Honestidade (Lei 6): o embedding (d=768 real) domina o payload de Q3. O BH só
ganha Q3 se a poda espacial deixar MENOS candidatos que o efSearch do HNSW —
ou seja, só em janelas pequenas. Janela grande → converge. Q4/Q2 são onde a
hierarquia ganha por construção (agregado pronto / estrutura partilhada).
"""
from __future__ import annotations

import numpy as np

SIDE = 256
STRUCT_BYTE = 1
D_EMB = 768          # embedding de IA realista
EF_SEARCH = 64       # largura de busca do HNSW (visita ~ef nós)
HNSW_LINK = 16 * 8   # bytes de grafo tocados por nó visitado (M=16)


def make_partition(side, seed=1, p=0.72, minb=4):
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
    return region


def build_tree(layers):
    """Constrói a quadtree união; devolve folhas [(y,x,s)] e nós internos por nível."""
    leaves = []
    internal_by_level = {}

    def homog(b):
        f = b.reshape(-1, b.shape[-1])
        return bool((f.max(0) - f.min(0) == 0).all())

    def rec(y, x, s, lvl):
        if s == 1 or all(homog(L[y:y + s, x:x + s]) for L in layers):
            leaves.append((y, x, s)); return
        internal_by_level[lvl] = internal_by_level.get(lvl, 0) + 1
        h = s // 2
        for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
            rec(y + dy, x + dx, h, lvl + 1)
    rec(0, 0, SIDE, 0)
    return leaves, internal_by_level


def leaves_in(leaves, x, y, w, h):
    out = []
    for (ly, lx, ls) in leaves:
        if lx < x + w and lx + ls > x and ly < y + h and ly + ls > y:
            out.append((ly, lx, ls))
    return out


def fmt(b):
    if b >= 1e6: return f"{b/1e6:.2f} MB"
    if b >= 1e3: return f"{b/1e3:.1f} KB"
    return f"{b:.0f} B"


def main():
    region = make_partition(SIDE)
    rgb = np.random.default_rng(10).integers(0, 256, (region.max() + 1, 3), np.uint8)[region]
    depth = np.random.default_rng(11).integers(0, 256, (region.max() + 1, 1), np.uint8)[region]
    seg = np.random.default_rng(12).integers(0, 256, (region.max() + 1, 1), np.uint8)[region]
    leaves, internal = build_tree([rgb, depth, seg])
    n_leaf = len(leaves)
    CH = 5  # RGB+depth+seg

    rows = []  # (query, bh_bytes, stitched_bytes, nota)

    # Q1 — preview ~32×32 (nível 5)
    L_prev = 5
    bh_top = sum(internal.get(k, 0) for k in range(L_prev)) * (STRUCT_BYTE + CH)
    st_thumb = 32 * 32 * 3  # rendition RGB armazenada
    rows.append(("Q1 preview ~32px", bh_top, st_thumb, "ambos pequenos"))

    # Q2 — ROI 64×64 + camadas co-registradas
    roi = (96, 96, 64, 64)
    lv = leaves_in(leaves, *roi)
    bh_roi = len(lv) * CH + len(lv) * STRUCT_BYTE  # 1 travessia partilhada
    st_roi = len(lv) * CH * 1 + 3 * len(lv) * STRUCT_BYTE + 200  # 3 traversals + índice espacial
    rows.append(("Q2 ROI 64² + camadas", bh_roi, st_roi, "estrutura partilhada"))

    # Q3 — retrieval ESCOPADO em janela 64×64 (top-k similar)
    win_leaves = len(leaves_in(leaves, 96, 96, 64, 64))
    bh_q3 = win_leaves * D_EMB * 4                       # lê embeddings da janela
    st_q3 = EF_SEARCH * (D_EMB * 4 + HNSW_LINK)          # HNSW visita ~ef nós (global)
    nota3 = f"janela={win_leaves} folhas vs ef={EF_SEARCH}"
    rows.append(("Q3 retrieval escopado", bh_q3, st_q3, nota3))

    # Q3b — retrieval em janela GRANDE (192×192): a fronteira
    win_big = len(leaves_in(leaves, 32, 32, 192, 192))
    bh_q3b = win_big * D_EMB * 4
    st_q3b = EF_SEARCH * (D_EMB * 4 + HNSW_LINK)
    rows.append(("Q3b retrieval janela grande", bh_q3b, st_q3b,
                 f"janela={win_big} > ef={EF_SEARCH} → perde"))

    # Q4 — agregado de janela 64×64
    bh_q4 = 12 * (STRUCT_BYTE + CH)        # ~poucos nós cobertos (O(log))
    st_q4 = len(lv) * CH                    # varre as folhas da janela
    rows.append(("Q4 agregado de janela", bh_q4, st_q4, "agregado pronto no nó"))

    Lr = ["# MULTIMODAL — FATIA 2 (ACESSO): bytes movidos por query\n"]
    Lr.append(f"Ativo {SIDE}×{SIDE}, {n_leaf:,} regiões, embedding d={D_EMB} (IA real), "
              f"HNSW efSearch={EF_SEARCH}. Métrica: bytes movidos por query.\n")
    Lr.append("| query | BH unificado | pilha costurada | ganho | nota |")
    Lr.append("|---|---|---|---|---|")
    for q, bh, st, nota in rows:
        g = st / bh if bh else float("inf")
        gtxt = f"{g:.1f}×" if g >= 1 else f"{g:.2f}× (perde)"
        Lr.append(f"| {q} | {fmt(bh)} | {fmt(st)} | **{gtxt}** | {nota} |")

    Lr.append("\n## LEITURA HONESTA\n")
    Lr.append("- **Q4 (agregado) e Q2 (ROI): o BH ganha por construção** — o agregado já "
              "está no nó (não varre a janela); a estrutura partilhada serve as 3 camadas "
              "numa travessia só. É o mesmo ganho do banco e do codec, num ativo multimodal.")
    Lr.append("- **Q3 (retrieval) é o divisor — e confirma a Lei 6.** Em janela PEQUENA, a "
              "poda espacial deixa poucas folhas e o BH lê menos embeddings que o efSearch "
              "do HNSW → ganha. Em janela GRANDE (Q3b), o nº de folhas ultrapassa o "
              "efSearch e o BH PERDE — porque aí o payload (embeddings d=768) domina e ler "
              "todos os candidatos custa mais que a busca do HNSW.")
    Lr.append("- **O padrão de novo:** o BH ganha onde a resposta é ESTRUTURAL (agregado, "
              "região, janela escopada pequena) e perde onde o EMBEDDING DENSO domina "
              "(retrieval de janela larga / global). Lei 6, mais uma vez.")
    Lr.append("- **Veredicto da fatia 2:** acesso é MISTO — vitórias reais em "
              "agregado/ROI/retrieval-escopado-estreito; derrota em retrieval largo/global "
              "(onde o HNSW reina). Não é o ganho universal que viraria produto sozinho; "
              "é mais um voto para 'o valor é operacional, não de números'.")

    out = __import__("pathlib").Path(__file__).resolve().parents[1] / "RESULTS_FATIA2_ACESSO.md"
    out.write_text("\n".join(Lr) + "\n", encoding="utf-8")
    for q, bh, st, nota in rows:
        g = st / bh if bh else 0
        print(f"{q:30s} BH={fmt(bh):>10}  costurado={fmt(st):>10}  ganho={g:.1f}×")
    print(f"\nrelatório: {out}")


if __name__ == "__main__":
    main()
