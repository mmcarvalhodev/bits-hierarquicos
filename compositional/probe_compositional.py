"""O BH no terreno-CASA: envelope algébrico vs payload denso.

A campanha toda testou o BH com payload RÍGIDO (cor, embedding, hash) — terreno
conexionista, onde a Lei 6 o afoga. O documento original era outra coisa: o nó
carrega uma EQUAÇÃO (composição de primitivos partilhados via operadores), não
um vetor. Aqui geramos dado COMPOSICIONAL e comparamos as duas representações.

Predição declarada: em dado composicional, o envelope algébrico é
ordens-de-grandeza menor E responde consultas estruturais que o denso NÃO
consegue. Ressalva: o dado é composicional POR CONSTRUÇÃO — a pergunta real é
quanto do dado do mundo é composicional (simbólico vs conexionista).
"""
from __future__ import annotations

import numpy as np

P = 256          # primitivos no vocabulário (partilhados)
N = 1_000_000    # conceitos
K = 3            # termos por composição (média)
D = 768          # dim do embedding denso (conexionista)
REF = 2          # bytes por referência a primitivo (uint16)
OP = 1           # byte por operador


def fmt(b):
    return f"{b/1e9:.2f} GB" if b >= 1e9 else f"{b/1e6:.1f} MB"


def main():
    rng = np.random.default_rng(7)
    # cada conceito = K primitivos + (K-1) operadores
    comps = rng.integers(0, P, (N, K), dtype=np.uint16)

    # ---- Representação A: DENSA (conexionista) ----
    dense = N * D * 4

    # ---- Representação B: ENVELOPE ALGÉBRICO (BH) ----
    # primitivos partilhados (uma vez) + a equação por conceito
    prim_table_atomic = P * 8                       # primitivo atômico (código)
    prim_table_emb = P * D * 4                       # OU primitivo com embedding (partilhado)
    eq_per_concept = K * REF + (K - 1) * OP
    envelope_atomic = prim_table_atomic + N * eq_per_concept
    envelope_emb = prim_table_emb + N * eq_per_concept

    # ---- Consulta estrutural: "conceitos contendo o primitivo X" ----
    X = 42
    # composicional: índice invertido (primitivo -> conceitos) ou varredura da eq
    comp_query_bytes = N * eq_per_concept           # pior caso: varre as equações
    # denso: o primitivo NÃO é recuperável do vetor — a consulta é IMPOSSÍVEL
    # sem manter a composição original; o denso precisaria de TODOS os conceitos
    # + um modelo p/ "explicar" cada vetor (na prática, não responde).

    L = ["# COMPOSICIONAL — envelope algébrico vs payload denso (terreno-casa do BH)\n"]
    L.append(f"{N:,} conceitos, {P} primitivos partilhados, K={K} termos/composição, "
             f"embedding denso d={D}.\n")
    L.append("## Storage\n")
    L.append("| representação | tamanho | vs denso |")
    L.append("|---|---|---|")
    L.append(f"| DENSA (vetor d={D} por conceito) | {fmt(dense)} | 1× |")
    L.append(f"| ENVELOPE (primitivo atômico + equação) | {fmt(envelope_atomic)} | "
             f"**{dense/envelope_atomic:,.0f}× menor** |")
    L.append(f"| ENVELOPE (primitivo c/ embedding partilhado) | {fmt(envelope_emb)} | "
             f"**{dense/envelope_emb:,.0f}× menor** |")

    L.append("\n## Consulta estrutural: 'conceitos que contêm o primitivo X'\n")
    L.append(f"- **Envelope:** nativo — o primitivo ESTÁ na equação. Varre {fmt(comp_query_bytes)} "
             f"(ou O(1) com índice invertido primitivo→conceitos).")
    L.append("- **Denso:** **IMPOSSÍVEL** sem a composição original. O primitivo não é "
             "recuperável do vetor — o denso perdeu a estrutura ao virar coordenada. "
             "Esta consulta não tem resposta no espaço denso.")

    L.append("\n## LEITURA HONESTA\n")
    L.append(f"- **No terreno composicional, o BH não empata — ESMAGA.** "
             f"{dense/envelope_atomic:,.0f}× menor (primitivo atômico), porque cada "
             f"conceito é uma equação de {eq_per_concept} bytes, não um vetor de "
             f"{D*4} bytes. O custo cresce com o nº de composições, não com a dimensão "
             f"(Lei 6 INVERTIDA: aqui a estrutura domina, o payload some).")
    L.append("- **E responde o que o denso não consegue:** 'quais conceitos usam o "
             "primitivo X?' é nativo no envelope e IMPOSSÍVEL no vetor denso. Não é "
             "'mais rápido' — é uma classe de consulta que só a representação "
             "composicional tem. Isso é vantagem estrutural REAL, não marginal.")
    L.append("- **A ressalva que mantém isto honesto:** o dado aqui é composicional POR "
             "CONSTRUÇÃO. O envelope ganha de graça porque eu o fiz composto. A pergunta "
             "empírica de verdade é: QUANTO do significado do mundo é composicional "
             "(simbólico) vs distribuído (conexionista)? Onde for composicional, o BH "
             "é a casa; onde for perceptual/contínuo (imagem, áudio, embedding aprendido), "
             "o denso captura nuance que o envelope perde.")
    L.append("- **O que isto REORGANIZA na campanha inteira:** testámos o BH em dado "
             "DENSO (pixels, embeddings) — seu pior terreno — e ele empatou/perdeu. O "
             "padrão de vitórias/derrotas tem UM eixo: **estruturado/composicional "
             "(ganha) vs denso/distribuído (perde)**. GPU/banco (escalares estruturados) "
             "ganharam; multimodal (embeddings densos) perdeu. O BH sempre foi o "
             "substrato de uma ÁLGEBRA composicional — exatamente o Intent AI — não um "
             "competidor de vector DB. Estávamos a testá-lo fora de casa o tempo todo.")

    out = __import__("pathlib").Path(__file__).resolve().parent / "RESULTS_COMPOSICIONAL.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"denso={fmt(dense)}  envelope_atomico={fmt(envelope_atomic)} "
          f"({dense/envelope_atomic:,.0f}×)  envelope_emb={fmt(envelope_emb)} "
          f"({dense/envelope_emb:,.0f}×)")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
