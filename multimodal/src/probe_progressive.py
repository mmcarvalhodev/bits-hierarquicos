"""Correção do probe — embedding PROGRESSIVO (Matryoshka), não full em todo nó.

O erro do probe original: injetar o embedding COMPLETO (d) em cada nó interno.
Isso provou só "injeção ingênua perde". Embeddings têm dimensão intrínseca
baixa (PCA, PQ, Matryoshka) — o prefixo carrega o essencial. Aqui o nó interno
guarda só um PREFIXO de dim p << d (suficiente p/ podar), a folha guarda o full.

Mede se o veredicto de storage MUDA quando paramos de tratar o embedding como
payload irredutível e o tratamos como o que ele é: infraestrutura compressível.
"""
from __future__ import annotations

import numpy as np

SIDE = 256
STRUCT_BYTE = 1
M_HNSW = 16
HNSW_BYTES = M_HNSW * 8
P_PREFIX = 64        # dim do prefixo Matryoshka no nó interno (poda)


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


def layer_from(region, ch, seed):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (region.max() + 1, ch), dtype=np.uint8)[region]


def _homog(b):
    f = b.reshape(-1, b.shape[-1])
    return bool((f.max(0) - f.min(0) == 0).all())


def count_union(layers, y, x, s):
    if s == 1 or all(_homog(L[y:y + s, x:x + s]) for L in layers):
        return 0, 1
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        a, b = count_union(layers, y + dy, x + dx, h)
        ni += a; nl += b
    return ni + 1, nl


def count_single(layer, y, x, s):
    if s == 1 or _homog(layer[y:y + s, x:x + s]):
        return 0, 1
    h = s // 2
    ni = nl = 0
    for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
        a, b = count_single(layer, y + dy, x + dx, h)
        ni += a; nl += b
    return ni + 1, nl


def run(d, p_prefix):
    region = make_partition(SIDE)
    rgb = layer_from(region, 3, 10)
    depth = layer_from(region, 1, 11)
    seg = layer_from(region, 1, 12)
    ni_u, nl_u = count_union([rgb, depth, seg], 0, 0, SIDE)
    ni_r, nl_r = count_single(rgb, 0, 0, SIDE)
    ni_d, nl_d = count_single(depth, 0, 0, SIDE)
    ni_s, nl_s = count_single(seg, 0, 0, SIDE)
    n_emb = nl_u

    # costurado (full HNSW, embedding canônico full)
    st = ((ni_r + ni_d + ni_s) * STRUCT_BYTE + (nl_r * 3 + nl_d + nl_s)
          + n_emb * d * 4 + n_emb * HNSW_BYTES + (SIDE // 8) ** 2 * 3 + n_emb * 20)

    # unificado INGÊNUO (full embedding em todo nó interno) — o probe original
    un_naive = (ni_u * STRUCT_BYTE + nl_u * 5 + n_emb * d * 4 + ni_u * d * 4)

    # unificado PROGRESSIVO (prefixo p no nó interno; full na folha)
    un_prog = (ni_u * STRUCT_BYTE + nl_u * 5 + n_emb * d * 4 + ni_u * p_prefix * 4)

    return n_emb, st, un_naive, un_prog


def fmt(b):
    return f"{b/1e6:.2f} MB" if b >= 1e6 else f"{b/1e3:.1f} KB"


def main():
    L = ["# MULTIMODAL — CORREÇÃO: embedding PROGRESSIVO vs injeção ingênua\n"]
    L.append(f"Nó interno guarda prefixo p={P_PREFIX} (Matryoshka), folha guarda full d. "
             "Compara o veredicto de storage ANTES (ingênuo) e DEPOIS (progressivo).\n")
    L.append("| d | costurado | unif. INGÊNUO | ganho | unif. PROGRESSIVO | ganho |")
    L.append("|---|---|---|---|---|---|")
    for d in (64, 256, 768, 1024, 4096):
        n, st, un_n, un_p = run(d, P_PREFIX)
        L.append(f"| {d} | {fmt(st)} | {fmt(un_n)} | {st/un_n:.2f}× | "
                 f"{fmt(un_p)} | **{st/un_p:.2f}×** |")

    L.append("\n## LEITURA HONESTA\n")
    L.append("- **A correção MOVE o veredicto.** O probe ingênuo perdia a partir de "
             "d≈128 porque cobrava full-d em cada nó interno. Com prefixo Matryoshka, o "
             "índice interno cai ~d/p× e o unificado volta a empatar/ganhar mesmo em "
             "d=1024-4096. O 'payload afoga' era em parte artefato da injeção ingênua.")
    L.append("- **MAS o ganho é só no ÍNDICE, não no bulk.** Os embeddings de folha "
             "(o grosso) são iguais dos dois lados — ambos guardam o canônico uma vez "
             "(Shannon de verdade). O unificado só ganha porque seu índice (prefixos "
             "internos) é mais barato que o HNSW+espacial+thumbnail. Ganho real, pequeno "
             "em absoluto.")
    L.append("- **E o SOTA já explora a redundância:** Matryoshka e PQ existem e são "
             "estado da arte. 'Embedding é compressível/hierárquico' é verdade — e já "
             "está implantado. O único que permanece aberto é a UNIFICAÇÃO: o mesmo "
             "prefixo servindo de embedding-progressivo E índice E estrutura, numa peça "
             "só, em vez de Matryoshka + HNSW + layout separados.")
    L.append("- **Conclusão corrigida:** a Lei 6 não estava errada, mas eu a apliquei "
             "mal — tratei infraestrutura compressível como payload. Corrigido, o storage "
             "passa de 'perde' para 'empata/ganha marginal no índice'. Reabre a porta uma "
             "fresta; não a escancara. O bulk (embedding de folha) continua sendo um "
             "empate de Shannon — lá ninguém ganha.")

    out = __import__("pathlib").Path(__file__).resolve().parents[1] / "RESULTS_CORRECAO_PROGRESSIVA.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    for d in (256, 1024, 4096):
        n, st, un_n, un_p = run(d, P_PREFIX)
        print(f"d={d:4d}: ingênuo={st/un_n:.2f}×  progressivo={st/un_p:.2f}×")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
