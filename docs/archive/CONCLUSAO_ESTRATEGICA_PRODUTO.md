# CONCLUSÃO ESTRATÉGICA — investigação de produto (Bits Hierárquicos)
## O ciclo mensurável fechado, e a única hipótese que sobra

**Autor:** Márcio M. Carvalho
**Data:** Junho 2026
**Escopo:** a etapa 3-4 (problema → mercado), depois de cinco terrenos medidos.

---

## 0. AS QUATRO FASES DA INVESTIGAÇÃO

```
Fase 1  "Existe algo aqui?" ............... SIM (padrão em 5 terrenos)
Fase 2  "Gera ganho mensurável?" .......... SIM (em vários casos)
Fase 3  "O ganho é novo?" ................. NA MAIOR PARTE, NÃO (SOTA já é hierárquico)
Fase 4  "Existe um produto?" .............. esta conclusão
```

O BH foi testado, no início, contra PROBLEMAS. No fim, contra MERCADOS. São
coisas diferentes — e a passagem de uma para outra é o que esta conclusão fecha.

---

## 1. O VEREDICTO MENSURÁVEL (storage + acesso)

Tentativa de produto: um substrato único co-registrado para dados multimodais
de IA, contra a pilha costurada (storage + HNSW + cache + índice espacial).

**Fatia 1 — STORAGE:** MORTA no regime real.
```
embedding d=8 → 4×  ·  d=128 → empate  ·  d=256 → 0,86× (perde)
Embeddings de IA reais são d=768-4096 → o substrato PERDE em storage.
```

**Fatia 2 — ACESSO:** MISTA.
```
Q1 preview ........... 7,6× (ganha — estrutural)
Q4 agregado .......... 3,2× (ganha — estrutural)
Q2 ROI+camadas ....... 2,1× (ganha — estrutural)
Q3 retrieval estreito  1,4× (ganha marginal)
Q3b retrieval largo .. 0,23× (PERDE — embedding denso domina)
```

**Síntese:** ganho real (2-8×) onde a resposta é ESTRUTURAL (preview, região,
agregado, janela estreita); derrota onde o EMBEDDING DENSO domina (retrieval
largo/global, onde o HNSW reina). Não é o ganho universal que viraria produto
sozinho.

---

## 2. A LEI QUE EXPLICA TUDO (Lei 6)

```
A hierarquia só rende quando a estrutura não é afogada pelo payload.
```

Reapareceu em TODOS os terrenos — codec (pixels), wafer (valores), GPU (dados
movidos), multimodal (embeddings). É a lei-mestra do limite do BH. E ela é
GENERATIVA — diz onde a vantagem mensurável pode existir e onde não vale testar:

```
PAYLOAD-PESADO (BH perde/empata) → pixels, embeddings, tensores densos, áudio
ESTRUTURA-PESADA (BH vive) ....... metadados, índices, telemetria, logs,
                                   séries de escalares, grafos esparsos, tick
```

**Implicação:** fomos caçar produto no terreno mais payload-pesado que existe
(IA multimodal densa). A Lei 6 prevê derrota lá. Se há produto-por-números,
está em dado ESTRUTURAL/ESPARSO — não em IA densa.

---

## 3. A ÚNICA HIPÓTESE AINDA VIVA

| hipótese | status | falsificável por probe? |
|---|---|---|
| "economiza storage" | **morta** | sim (fatia 1) |
| "move menos dados/query" | **mista/fraca** | sim (fatia 2) |
| **"reduz complexidade sistêmica"** (1 fonte vs 4) | **VIVA** | **não** |
| **"elimina sync índice↔cache↔storage"** | **VIVA, dor real** | **não** |

A hipótese mais forte que ainda não foi falsificada **não é de números** — é
OPERACIONAL: uma única fonte de verdade em vez de sincronizar quatro sistemas
que podem divergir. É forte precisamente porque a Lei 6 não a toca: a dor de
manter storage + índice + cache + renditions consistentes não é sobre payload
nem estrutura — é sobre QUANTOS sistemas podem ficar fora de sincronia.

**Precedente:** Docker e Kubernetes não economizam nada mensurável; venceram
por eliminar uma classe de problema operacional. O BH-como-produto, se existir,
é desse tipo.

**A verdade dura:** essa hipótese **não se mata nem se confirma com um probe.**
Validar "reduz complexidade operacional" exige construir os dois stacks, operá-
los por meses, e contar incidentes de divergência / custo de sync / staleness.
Não é benchmark — é a própria aposta de produto.

---

## 4. ONDE A INVESTIGAÇÃO CHEGOU (uma fronteira de TIPO)

```
A parte MENSURÁVEL (storage, acesso) está fechada — e é majoritariamente
   negativa em dado denso, por causa da Lei 6.
A parte VIVA (operação, consistência) é NÃO-MENSURÁVEL por probe — é uma
   aposta arquitetural, validável só construindo.
```

A decisão deixou de ser "o que o próximo experimento diz" e passou a ser:
**"queres fazer a aposta de fundador — construir e operar um substrato único na
hipótese de simplicidade operacional?"** Isso é risco, não medição.

E há um caminho alternativo que a Lei 6 abre, ainda mensurável: **pivotar para
dado estrutura-pesada** (telemetria, logs, séries, grafos esparsos, metadados),
onde o ganho de números SOBREVIVE — em vez de insistir em IA densa, onde a Lei
6 garante a derrota.

---

## 5. O QUE FOI ALCANÇADO (e por que é raro)

Mesmo que o veredicto final seja *"princípio interessante, sem vantagem
econômica suficiente em dado denso"*, isto é uma conclusão FORTE:

```
- uma tese formulada, testada em 5 terrenos, contra o estado da arte;
- ganhos medidos onde existem (48× codec, 52.000× Merkle, 1.750× GPU);
- fronteiras marcadas onde não existem (foto natural, retrieval denso);
- uma lei-mestra (Lei 6) que prevê onde procurar e onde não;
- duas hipóteses de produto mortas com número, uma viva e nomeada.
```

Pouquíssimas ideias chegam a este grau de escrutínio. O conhecimento NEGATIVO
("isso não funciona aqui, e eis exatamente por quê") vale mais, na busca de
produto, que um conhecimento positivo vago.

---

## 6. RECOMENDAÇÃO HONESTA

```
1. O produto-por-números em IA densa: NÃO. A Lei 6 fecha isso.
2. A aposta operacional (1 substrato vs 4 sistemas): VIVA, mas é aposta de
   fundador — só se valida construindo, e compete por TCO/ops, não por algoritmo.
3. O pivô da Lei 6 (dado estrutura-pesada): o lugar mais provável de um ganho
   de números real — vale uma fatia nova SE quiseres continuar medindo.
4. O valor já realizado: um framework de leitura de dados + um método de
   investigação honesta — esse valor independe de haver produto.
```

---

*O princípio é matéria-prima; o produto é o que vende. A investigação provou o
princípio e mapeou seu valor com precisão — e mostrou que, em dado denso de IA,
o produto-por-números não está lá. O que resta é uma aposta operacional (não
mensurável por probe) ou um pivô para dado esparso (mensurável, não testado).
Em qualquer caso: a tese foi perseguida até o fim. Isso é raro.*
