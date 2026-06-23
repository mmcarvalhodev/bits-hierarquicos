# BH DB MVP — RESULTADOS

Dataset: 1,000,000 linhas · bloco 1,024 · árvore binária de agregação.
Métrica primária: **linhas lidas** (independe de linguagem). Tempo: NumPy nos dois lados; o full scan é vetorizado em C, então o tempo favorece o baseline — a métrica honesta é linhas lidas.

## VEREDICTO POR ALEGAÇÃO

- **D1 (agregação ≈ thumbnail): CONFIRMADA** — agregados lêem ≤ 2 blocos de fronteira, nunca o range/tabela.
- **D2 (filtro seletivo ≈ ROI): CONFIRMADA** — poda no eixo organizado / coluna correlacionada ganha ≥ 3× do full scan.
- **D3 (fronteira declarada): REPORTADA** — eixo não-agregado, valor independente ou baixa seletividade → poda inútil, lê ~tudo. Esperado, medido, não escondido.

## QUERIES — linhas lidas (BH vs plano)

| query | descrição | alegação | BH lê | plano lê | ganho | tempo BH/plano (ms) |
|---|---|---|---|---|---|---|
| Q1 | SUM global | D1 | 0 | 1,000,000 | ∞ | 0.0 / 0.2 |
| Q2 | SUM range 10% | D1 | 1,564 | 99,868 | 64× | 0.0 / 0.0 |
| Q3a | COUNT key in 2% | D2 | 2,048 | 1,000,000 | 488× | 0.0 / 1.7 |
| Q3b | COUNT val_trend>p99 | D2 | 92,736 | 1,000,000 | 11× | 0.3 / 0.8 |
| Q4a | COUNT val_rand>p99 | D3 | 1,000,000 | 1,000,000 | 1× | 3.5 / 0.8 |
| Q4b | COUNT region==3 | D3 | 1,000,000 | 1,000,000 | 1× | 2.7 / 0.8 |
| Q5 | COUNT region==3 (region_counts) | D2+ | 0 | 1,000,000 | ∞ | 0.0 / 0.8 |
| Q4c | COUNT val_trend>p50 | D3 | 598,592 | 1,000,000 | 2× | 2.0 / 0.8 |

## A MESMA ÁRVORE, QUATRO LEITURAS

Nenhum índice separado foi construído. A MESMA estrutura respondeu:
- **agregado** (Q1, Q2) — lendo nós internos, ~0 linhas;
- **poda multi-coluna** (Q3a, Q3b, Q4a) — lendo só os ramos que sobrevivem ao min/max de cada coluna materializada;
- **scan cru** — lendo todos os blocos (o baseline interno).
- **agregado categórico** (Q5) — a query que perdia em Q4b vira leitura de raiz quando `region_counts` existe no nó.
Uma estrutura, várias interpretações — a leitura é escolhida pelo objetivo da query. É a tese do paradigma, agora em banco de dados.

## LEITURA HONESTA

- **D1/D2 ganham por construção** — o agregado vive nos nós; o filtro no eixo certo poda subárvores. Ganho ∝ fanout·log n (agregação) e ∝ seletividade (poda).
- **D3 é a mesma fronteira do codec** — assim como textura natural derrota a rampa, valor independente da chave derrota a poda por min/max. A interpretação (árvore por key) não casa com a query (filtro por valor espalhado ou por região). Endereço vazio na biblioteca, não falha da abordagem: uma árvore organizada por região, ou um índice de valor, casaria — e é literalmente o que bancos reais mantêm (múltiplos índices = múltiplas interpretações materializadas).
- **Não inventa um banco novo** — Parquet/zone-maps/segment-trees já fazem isto. O que o PoC prova é a UNIFICAÇÃO: decode progressivo de imagem e poda de agregação em banco são a MESMA leitura-por-objetivo sobre hierarquia grátis.
