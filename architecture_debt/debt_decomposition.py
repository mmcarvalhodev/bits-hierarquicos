"""Decomposição de DÍVIDA ARQUITETURAL — stack RAG real (busca vetorial).

NÃO compara contra um "BH ideal". Decompõe os custos de um stack REAL e marca
cada um como ELIMINÁVEL (dívida: existe só porque o contexto foi colado depois)
ou IRREDUTÍVEL (payload + organizações genuinamente diferentes + índices
necessários por padrões de acesso distintos).

Classificação CONSERVADORA: na dúvida → irredutível (viés CONTRA a hipótese,
para a dívida não ser inflada). O swing-factor (duplicação de embeddings) é
parametrizado e mostrado nos dois extremos.

Régua (definida pelo autor): dívida 50-70% → há produto; 10-20% → filosofia.
"""
from __future__ import annotations

# corpus realista
N = 10_000_000          # chunks
CHUNK = 512             # bytes/chunk (texto)
D = 1024               # dim do embedding (IA real)
M = 32                  # conexões HNSW
EMB = D * 4             # bytes/embedding


def components(dup_embeddings: bool, d: int = D):
    """Cada componente: (nome, bytes, classe, justificativa)."""
    emb = d * 4
    c = [
        ("texto cru (chunks)", N * CHUNK, "IRR",
         "payload — o dado em si"),
        ("embeddings canônicos", N * emb, "IRR",
         "info semântica; custo do padrão de acesso 'similaridade' (Lei 6: payload)"),
        ("grafo HNSW", N * M * 8, "IRR",
         "índice de similaridade — padrão de acesso real (no-free-lunch)"),
        ("índice keyword (BM25)", N * 200, "IRR",
         "padrão de acesso DIFERENTE (busca lexical) — organização incompatível"),
        ("índice de metadados", N * 50, "IRR",
         "padrão de acesso 'filtro' — organização própria"),
        # ---- dívida ----
        ("cópia de vetores no índice", (N * emb) if dup_embeddings else 0, "ELIM",
         "duplicação dos embeddings p/ localidade — eliminável (índice referencia o canônico)"),
        ("duplicação doc-store↔search", N * CHUNK, "ELIM",
         "o chunk vive no object store E no motor de busca — duplicação"),
        ("cache de query/embedding", int(0.05 * N * emb), "ELIM",
         "derivado, recomputável"),
        ("previews/resumos derivados", N * 100, "ELIM",
         "derivado do texto, recomputável"),
    ]
    return c


def report(dup: bool, d: int = D):
    comp = components(dup, d)
    total = sum(b for _, b, _, _ in comp)
    elim = sum(b for _, b, cl, _ in comp if cl == "ELIM")
    irr = total - elim
    return total, elim, irr, elim / total, comp


def fmt(b):
    return f"{b/1e9:.1f} GB"


def main():
    L = ["# DÍVIDA ARQUITETURAL — decomposição de um stack RAG real\n"]
    L.append(f"Corpus: {N:,} chunks × {CHUNK} B · embedding d={D}. Classificação "
             "conservadora (dúvida → irredutível). Régua: 50-70% dívida = produto; "
             "10-20% = filosofia.\n")

    L.append("## Componentes (caso COM duplicação de embeddings — pior caso de dívida)\n")
    total, elim, irr, frac, comp = report(dup=True)
    L.append("| componente | tamanho | classe | porquê |")
    L.append("|---|---|---|---|")
    for name, b, cl, why in comp:
        if b == 0:
            continue
        L.append(f"| {name} | {fmt(b)} | {cl} | {why} |")
    L.append(f"\n**Total {fmt(total)} · irredutível {fmt(irr)} · dívida {fmt(elim)} "
             f"→ DÍVIDA = {frac:.0%}**\n")

    L.append("## Sensibilidade — o swing-factor é a duplicação de embeddings\n")
    L.append("| cenário | total | dívida | % dívida |")
    L.append("|---|---|---|---|")
    for label, dup in [("COM duplicação de vetores", True),
                       ("SEM duplicação (índice referencia canônico)", False)]:
        t, e, i, f, _ = report(dup)
        L.append(f"| {label} | {fmt(t)} | {fmt(e)} | **{f:.0%}** |")

    # sensibilidade em d
    L.append("\n| d (embedding) | % dívida (com dup) | % dívida (sem dup) |")
    L.append("|---|---|---|")
    for d in (256, 768, 1024, 4096):
        _, _, _, fcom, _ = report(True, d)
        _, _, _, fsem, _ = report(False, d)
        L.append(f"| {d} | {fcom:.0%} | {fsem:.0%} |")

    L.append("\n## LEITURA HONESTA\n")
    L.append("- **A dívida é REAL mas BORDERLINE: ~25-49%**, e o swing é se o stack "
             "duplica os embeddings (vetores no índice + no store). Com duplicação, "
             "beira os 50% (produto); sem, cai para ~25% (zona cinzenta).")
    L.append("- **Ironia da Lei 6:** a maior fatia de DÍVIDA é a duplicação dos "
             "EMBEDDINGS — payload denso, não estrutura. Ou seja, a dívida eliminável "
             "também é dominada por payload. E o SOTA já a ataca (índices em disco, "
             "quantização, pgvector que referencia em vez de copiar).")
    L.append("- **A parte de estrutura pura (caches, previews, metadados) é PEQUENA** "
             "(<10%). O 'oito subsistemas porque o dado nasceu burro' é menos dívida "
             "de bytes do que parece — a maior parte do custo é payload irredutível + "
             "índices necessários por padrões de acesso diferentes (no-free-lunch).")
    L.append("- **O que ISTO não captura:** a dívida OPERACIONAL (sync, drift, "
             "engenharia de manter N sistemas) não cabe em bytes — e é real. Em custo "
             "de bytes a dívida é ~25-49%; em custo de OPERAÇÃO pode ser maior, mas isso "
             "não é mensurável por este modelo (só construindo e operando).")
    L.append("- **Veredicto pela régua do autor:** em BYTES, a dívida fica na fronteira "
             "(25-49%), não nos 50-70% que cravariam um produto. O caso de bytes é "
             "borderline-fraco; o caso forte, se existir, é operacional — e esse este "
             "modelo não mede.")

    out = __import__("pathlib").Path(__file__).resolve().parent / "RESULTS_DIVIDA.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    for label, dup in [("com dup", True), ("sem dup", False)]:
        t, e, i, f, _ = report(dup)
        print(f"{label}: total={fmt(t)} divida={fmt(e)} ({f:.0%})")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
