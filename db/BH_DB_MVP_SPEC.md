# BH DB — SPEC DO MVP
## Prova de generalidade: Bits Hierárquicos aplicados a consulta de dados

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Origem:** `../arquitetura_bits_hierarquicos.md` + MVP codec (`../RESULTS_MVP_BH_CODEC.md`)
**Status:** SPEC — segundo terreno do paradigma

---

## 0. POR QUE ESTE PoC EXISTE

O MVP codec provou o paradigma em UM terreno (imagem). Este PoC testa a
afirmação mais forte: **"não é um algoritmo, é uma forma de ler dados"** —
levando a MESMA moldura a um domínio que parece sem relação com imagem.

```
Se a mesma moldura (biblioteca de interpretações + hierarquia grátis +
seleção por objetivo) ganha em banco de dados como ganhou em codec,
então a generalidade deixa de ser afirmação e vira demonstração.
```

A tradução é direta:

```
thumbnail (lê o topo)        → AGREGAÇÃO (lê nós internos, não as linhas)
ROI (lê um ramo)             → FILTRO SELETIVO (poda por min/max)
decode progressivo           → RESPOSTA APROXIMADA (níveis rasos, refina)
nó carrega cor média         → nó carrega min/max/sum/count do sub-conjunto
biblioteca de interpretações → a MESMA árvore lida como agregado / como
                               índice de poda / como linhas cruas
```

**Nota de honestidade (igual ao codec):** bancos reais já fazem isto —
zone maps do Parquet, segment trees, OLAP cubes. Este PoC NÃO inventa um
banco revolucionário. Prova que decode-progressivo-de-imagem e
poda-de-agregação-em-banco são A MESMA COISA sob o paradigma. O que é
original não é a engenharia; é a unificação.

---

## 1. ALEGAÇÕES FALSIFICÁVEIS

Métrica primária: **linhas lidas** para responder a query (justa, independe
de linguagem — o análogo exato do "bytes lidos" do codec). Em banco real,
linhas mapeiam para páginas/IO; nós da árvore para metadados pequenos.

```
D1 — AGREGAÇÃO É BARATA (≈ thumbnail)
     SUM/COUNT/MIN/MAX globais ou por range são respondidos lendo nós
     internos (agregados), não as N linhas.
     Sucesso: agregado global lê ~0 linhas; agregado de range lê ≤ 2 blocos
     de fronteira (≪ tamanho do range).
     Fracasso: se precisar varrer o range inteiro.

D2 — FILTRO SELETIVO PODA (≈ ROI)
     WHERE no eixo organizado (ou em coluna correlacionada) lê só os ramos
     que podem casar, via min/max.
     Sucesso: linhas lidas ∝ seletividade + fronteira; ganho grande sobre
     full scan.
     Fracasso: se ler ~tudo mesmo sendo seletivo no eixo certo.

D3 — A PERDA DECLARADA (≈ textura de foto natural)
     Filtro num eixo que a árvore NÃO organiza (ex.: região, não agregada),
     OU filtro pouco seletivo (casa ~tudo) → poda inútil.
     Esperado: lê ≥ full scan + overhead. NÃO é pass/fail — é a FRONTEIRA
     do paradigma, medida e reportada, não escondida.
```

---

## 2. ESTRUTURA

```
Tabela sintética (log de eventos), ordenada pela chave:
  key       int64    timestamp monotónico (eixo de organização)
  region    int8     categórico (8 regiões) — NÃO agregado (demonstra D3)
  val_trend float64  correlacionado com key (poda funciona — D2)
  val_rand  float64  independente da key (poda fraca — D3)

Árvore de agregação (análogo 1D da pirâmide do codec):
  - folhas = blocos de B linhas (B=1024) — "row groups"
  - cada nó carrega: key_min/max, val_min/max, val_sum, count
  - fanout binário sobre os blocos → ~log2(N/B) níveis
  - a MESMA árvore serve as três leituras
```

## 3. AS TRÊS INTERPRETAÇÕES (mesma estrutura, leitura por objetivo)

```
aggregate_range  → usa nós cobertos; lê linhas cruas só nos 2 blocos de
                   fronteira. (D1)
prune_filter     → desce a árvore; poda subárvore se min/max exclui o
                   predicado; lê linhas só dos blocos que sobrevivem. (D2/D3)
raw_scan         → lê todos os blocos = full table scan (o baseline). 
```

## 4. BASELINE

```
Tabela plana ordenada:
  full_scan       lê N linhas (o "decodar tudo")
  range_scan      lê as linhas do range (binary search + varre a fatia)
  filter_scan     lê N linhas (checa todas)
```

## 5. QUERIES MEDIDAS

```
Q1  agregado global       SUM(val_trend)                    → D1
Q2  agregado de range     SUM(val_trend) WHERE key in 10%   → D1
Q3a filtro no eixo        COUNT WHERE key in faixa estreita → D2
Q3b filtro correlacionado COUNT WHERE val_trend > p99       → D2
Q4a filtro independente   COUNT WHERE val_rand > p99        → D3 (poda fraca)
Q4b filtro fora-de-eixo   COUNT WHERE region == r           → D3 (sem poda)
Q4c filtro pouco seletivo COUNT WHERE val_trend > mediana   → D3 (casa ~tudo)
```

## 6. MÉTRICAS E VEREDICTO

```
Por query: linhas lidas (BH vs baseline), nós lidos, fator de ganho, tempo.
Veredicto por alegação: CONFIRMADA / PARCIAL / REFUTADA com números.
D3 reportada como FRONTEIRA (esperado perder), não como falha.
```

## 7. ESTRUTURA DO PROJETO

```
db/
├── BH_DB_MVP_SPEC.md
├── src/
│   ├── bhdb/
│   │   ├── table.py     # dataset sintético + baselines planos
│   │   └── tree.py      # AggregateTree (segment tree) + 3 leituras
│   └── bench/
│       └── harness.py   # roda Q1-Q4, emite RESULTS.md
├── tests/
│   ├── test_correctness.py  # BH == plano (exato), set de matches igual
│   └── test_reads.py        # D1/D2 lêem fração; D3 não poda
└── RESULTS.md
```

Stack: Python 3.13 + NumPy. Standalone. Gate: correctness exata (BH bate
o plano em todo agregado e todo set de matches) antes de qualquer medição.

---

*O codec leu pixels pela convenção que minimiza bytes×erro. O banco lê
linhas pela convenção que minimiza linhas×query. Mesma moldura, terreno
diferente. É a tese: não é o algoritmo, é a forma de ler.*
