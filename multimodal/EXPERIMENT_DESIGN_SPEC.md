# EXPERIMENT DESIGN — substrato unificado vs pilha costurada (dados multimodais de IA)
## A pergunta de produto: um substrato BH custa menos que costurar 4 sistemas SOTA?

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Origem:** a etapa 3 ("achar a aplicação com vantagem real") — o único canto
onde "ganho vs estado da arte" pode ser positivo, porque o estado da arte
aqui é uma COLCHA DE RETALHOS, não um sistema único.

---

## 0. A PERGUNTA (e por que não é as outras)

```
NÃO perguntamos: "o BH bate o HNSW / o JPEG / o vector DB?"  (perde — são SOTA)
PERGUNTAMOS:     "rodar UM substrato co-registrado custa menos no TOTAL que
                  costurar os 4 sistemas separados que hoje fazem o trabalho?"
```

Produtos ganham por **integração**, não por algoritmo (Datadog não inventou
monitoramento; Snowflake não inventou SQL colunar — integraram). O valor é
TCO + simplicidade operacional: 1 substrato vs 4 sistemas costurados.

---

## 1. A CARGA (workload realista e reusado)

Um ativo multimodal de IA, escrito uma vez, **consultado muitas vezes**:
memória de agente / compreensão de vídeo / IA geoespacial. Camadas
**co-registradas** (mesma cena, mesmas bordas):

```
RGB ............ 3 canais   (o quadro)
profundidade ... 1 canal    (depth do modelo)
segmentação .... 1 canal    (máscara semântica)
embeddings ..... d-dim/região (vetores semânticos por região)
saliência ...... 1 canal    (mapa de atenção)         [opcional]
```

Consultas (o mix), TODAS espaço-temporalmente escopadas:
```
Q1 preview progressivo / LOD     (scrubbing, UI, thumbnail)
Q2 fetch de região + suas camadas ("o que há aqui?")
Q3 retrieval ESCOPADO            ("regiões similares a X nesta janela")
Q4 agregado temporal             ("resumo desta janela de tempo")
```

**Fronteira declarada (honestidade):** retrieval semântico GLOBAL (achar os
K mais similares em TODO o dataset) é trabalho do HNSW e fica FORA do escopo —
ou é tratado por uma camada semântica grosseira. O substrato BH compete nas
consultas ESCOPADAS, que são a maioria em memória de agente / vídeo / geo.

---

## 2. O BASELINE COSTURADO (as 4 peças SOTA)

```
1. Object storage   um arquivo por modalidade (RGB, depth, seg, embeddings)
                    cada um com sua estrutura própria — replicada.
2. Vector index     HNSW sobre os embeddings (p/ Q3). Grafo separado:
                    overhead ~ n × M × 8 B (M≈16, modelo publicado).
3. Renditions/cache thumbnails/previews pré-computados (p/ Q1). Armazenados.
4. Índice espacial  estrutura separada p/ lookup de região/tempo (Q2/Q4).

TCO_costurado = Σ storage das 4 peças + Σ trabalho de acesso por query
                (cada query bate na peça relevante).
```

## 3. O SUBSTRATO BH UNIFICADO

```
UMA hierarquia espaço-temporal co-registrada:
  - estrutura partilhada (união sobre camadas, base+refinamento)
  - payload por camada/folha (RGB, depth, seg, embedding)
  - resumo no nó: agregado (Q4) + embedding representativo da subárvore (Q3)
Serve:
  Q1 = ler o topo (preview FREE — sem rendition armazenada)
  Q2 = ler um ramo (ROI + camadas co-registradas)
  Q3 = podar pela hierarquia + comparar embedding local (índice FREE p/ escopo)
  Q4 = ler o agregado do nó

TCO_unificado = storage da 1 hierarquia + trabalho de acesso por query.
O que SOME vs costurado: renditions (preview é free), índice espacial
(a hierarquia é o índice), estrutura replicada (partilhada). O que PERMANECE:
os payloads (Shannon) e — se houver retrieval global — o HNSW.
```

## 4. MÉTRICA (TCO)

```
STORAGE      bytes totais: unificado vs Σ das 4 peças.
ACESSO       bytes movidos por tipo de query, somados sobre o mix.
OPERACIONAL  nº de sistemas a manter (1 vs 4) — qualitativo, não medido.
```

## 5. CRITÉRIOS DE DECISÃO (declarados ANTES de medir)

```
VENCE (há produto) se:
  storage_unificado ≤ storage_costurado  E  acesso_unificado ≤ costurado,
  no mix escopado, em dado co-registrado.

PERDE (não há produto) se:
  - conteúdo não-co-registrado (a união super-subdivide — fronteira W3); ou
  - a carga é dominada por retrieval GLOBAL (precisa de HNSW de qualquer forma); ou
  - cada peça costurada comprime tão bem que a soma < o substrato (lição do portfólio).
```

## 6. FATIAS

```
Fatia 1  STORAGE  unificado vs costurado (4 peças) — o sinal mais decisivo e barato.
Fatia 2  ACESSO   bytes movidos por query no mix escopado.
Fatia 3  TEMPORAL stack de frames (coerência temporal) — o caso do vídeo.
Fatia 4  TCO real custo em $ (storage cloud + compute por query) — só se 1-3 verdes.
```

## 7. O QUE ISTO DECIDE

```
Se as fatias 1-2 forem VERDES → existe um "YT Radar dos BH": vale virar etapa 3
  (protótipo de produto, benchmarkado contra a pilha costurada real).
Se forem VERMELHAS → o princípio tem valor intelectual, não de produto. Para aqui
  com honestidade, em vez de construir "mais um vector DB" e perder.
```

---

*Não competimos peça-a-peça (perderíamos para cada SOTA). Competimos na pilha
inteira costurada. Se o substrato unificado custar menos que a soma das partes,
o valor é de produto — não de paper.*
