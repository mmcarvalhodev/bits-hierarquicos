# COMPOSICIONAL — envelope algébrico vs payload denso (terreno-casa do BH)

1,000,000 conceitos, 256 primitivos partilhados, K=3 termos/composição, embedding denso d=768.

## Storage

| representação | tamanho | vs denso |
|---|---|---|
| DENSA (vetor d=768 por conceito) | 3.07 GB | 1× |
| ENVELOPE (primitivo atômico + equação) | 8.0 MB | **384× menor** |
| ENVELOPE (primitivo c/ embedding partilhado) | 8.8 MB | **350× menor** |

## Consulta estrutural: 'conceitos que contêm o primitivo X'

- **Envelope:** nativo — o primitivo ESTÁ na equação. Varre 8.0 MB (ou O(1) com índice invertido primitivo→conceitos).
- **Denso:** **IMPOSSÍVEL** sem a composição original. O primitivo não é recuperável do vetor — o denso perdeu a estrutura ao virar coordenada. Esta consulta não tem resposta no espaço denso.

## LEITURA HONESTA

- **No terreno composicional, o BH não empata — ESMAGA.** 384× menor (primitivo atômico), porque cada conceito é uma equação de 8 bytes, não um vetor de 3072 bytes. O custo cresce com o nº de composições, não com a dimensão (Lei 6 INVERTIDA: aqui a estrutura domina, o payload some).
- **E responde o que o denso não consegue:** 'quais conceitos usam o primitivo X?' é nativo no envelope e IMPOSSÍVEL no vetor denso. Não é 'mais rápido' — é uma classe de consulta que só a representação composicional tem. Isso é vantagem estrutural REAL, não marginal.
- **A ressalva que mantém isto honesto:** o dado aqui é composicional POR CONSTRUÇÃO. O envelope ganha de graça porque eu o fiz composto. A pergunta empírica de verdade é: QUANTO do significado do mundo é composicional (simbólico) vs distribuído (conexionista)? Onde for composicional, o BH é a casa; onde for perceptual/contínuo (imagem, áudio, embedding aprendido), o denso captura nuance que o envelope perde.
- **O que isto REORGANIZA na campanha inteira:** testámos o BH em dado DENSO (pixels, embeddings) — seu pior terreno — e ele empatou/perdeu. O padrão de vitórias/derrotas tem UM eixo: **estruturado/composicional (ganha) vs denso/distribuído (perde)**. GPU/banco (escalares estruturados) ganharam; multimodal (embeddings densos) perdeu. O BH sempre foi o substrato de uma ÁLGEBRA composicional — exatamente o Intent AI — não um competidor de vector DB. Estávamos a testá-lo fora de casa o tempo todo.
