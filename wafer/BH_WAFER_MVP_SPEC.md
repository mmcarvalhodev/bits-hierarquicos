# BH WAFER — SPEC DO MVP
## Quarto terreno: múltiplas camadas co-registradas sobre UMA hierarquia

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Origem:** a tese-mãe — "dado-wafer": múltiplos significados/camadas no mesmo
dado gravado, partilhando a estrutura.

---

## 0. A IDEIA

Hoje um dado é construído pensando exclusivamente em si. Mas várias camadas
**co-registradas** (da mesma cena/entidade) partilham a MESMA estrutura
espacial — e poderiam ser gravadas sobre UMA hierarquia, lida por lentes
diferentes:

```
UMA quadtree (a subdivisão), gravada uma vez.
Em cada folha: K payloads — um por camada.
lente "RGB"   → a foto
lente "IR"    → infravermelho
lente "máscara" → segmentação
lente "profundidade" → terreno
```

Aplicação hoje, com IA: modelos produzem pilhas co-registradas (RGB +
profundidade + segmentação + mapas de saliência + embeddings espaciais) da
MESMA imagem. Ninguém guarda isso partilhando estrutura — cada camada é um
arquivo com sua própria indexação replicada.

## 1. O TETO (Shannon — declarado antes de medir)

N bits carregam ≤ N bits. O wafer **NÃO** comprime conteúdo independente de
graça. O que ele partilha é a ESTRUTURA (a subdivisão), não o payload:

```
GRÁTIS:  a hierarquia/subdivisão, gravada 1× em vez de K×.
COBRADO: os payloads — cada camada paga seus próprios bits (Shannon).
```

## 2. ALEGAÇÕES FALSIFICÁVEIS

Métrica: bytes de estrutura + bytes de payload (separados, honestos).

```
W1 — AMORTIZAÇÃO DE ESTRUTURA (camadas co-registradas)
     Camadas que subdividem nos MESMOS lugares → wafer grava a estrutura 1×.
     Sucesso: wafer < soma dos K arquivos independentes; ganho ∝ fração que
     é estrutura.

W2 — O TETO DE SHANNON (honestidade)
     O payload total do wafer ≈ soma dos payloads independentes — não há
     compressão mágica de conteúdo. Só a estrutura é partilhada.

W3 — A FRONTEIRA (camadas NÃO co-registradas)
     Camadas com bordas desalinhadas → subdivisão-união super-subdivide →
     wafer PIOR que independente. Esperado, medido, não escondido.
```

## 3. ESTRUTURA

```
Quadtree com subdivisão-UNIÃO: um nó é folha sse TODAS as camadas são
homogêneas nele (dentro do threshold). Estrutura partilhada; K payloads/folha.
Baseline: cada camada com sua PRÓPRIA quadtree (estrutura replicada K×).
```

## 4. CENÁRIOS

```
A) co-registrado   — K camadas partilham a MESMA partição (bordas alinhadas)
B) desalinhado     — K camadas com partições independentes (a fronteira W3)
C) foto + derivada — RGB real + 2ª camada co-registrada (caso realista)
```

## 5. PROJETO

```
wafer/
├── BH_WAFER_MVP_SPEC.md
├── src/bhwafer/wafer.py    # quadtree união + contabilidade estrutura/payload
├── src/bench/harness.py    # cenários A/B/C, emite RESULTS.md
├── tests/test_wafer.py     # reconstrução exata por camada; estrutura partilhada
└── RESULTS.md
```

Stack: Python 3.13 + NumPy. Gate: cada camada reconstrói exata a partir do
wafer (lossless) antes de medir.

---

*O wafer não cria informação — partilha estrutura. O ganho é real onde as
camadas são co-registradas; some onde não são. A magia e o teto na mesma
medição.*
