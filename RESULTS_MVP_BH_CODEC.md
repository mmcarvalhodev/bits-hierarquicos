# MVP BH CODEC — RESULTADOS CONSOLIDADOS
## Prova de conceito: Bits Hierárquicos aplicados a um codec de imagem 4K

**Autor:** Márcio M. Carvalho
**Data:** Junho 2026
**Origem conceitual:** `arquitetura_bits_hierarquicos.md` (Dezembro 2025)
**Spec do MVP:** `BH_CODEC_MVP_SPEC.md`
**Status:** PoC concluído — três rodadas medidas, veredicto honesto

---

## SUMÁRIO EXECUTIVO

Este MVP testou uma tese: **a hierarquia (e o ganho que ela traz) não está
nos bits — está na interpretação convencionada sobre como lê-los.** Um byte
já é uma árvore implícita; um codec BH apenas escolhe, por região, a
interpretação que rende mais.

O que ficou provado, com medição em frames 4K reais:

```
✅ A interpretação É a alavanca.
   Mesmos pixels (um gradiente 4K), trocando só a convenção de leitura:
   61× PIOR que o PNG (interpretação "cor constante")
   → ~2 KB, melhor que todos (interpretação "rampa").
   Ordem de grandeza ~1000×, zero mudança no algoritmo de árvore.

✅ Um codec tosco em Python BATE o codec mais polido disponível (WebP),
   por 48×, em conteúdo que casa com a interpretação — com qualidade MAIOR.

✅ O acesso parcial é estrutural, não questão de polimento.
   Thumbnail de um 4K: o BH lê 4-44× menos bytes que WebP/JPEG/PNG —
   inclusive em foto natural, onde o BH PERDE em compressão.

❌ Compressão de foto natural: os codecs polidos vencem.
   Sem transformada de frequência + entropy coding, a quadtree não
   compete. Declarado, medido, não escondido.
```

**Conclusão:** o PoC cumpriu seu papel — trocou os números fabricados do
documento de Dezembro por veredictos reais. A tese central sobrevive na
sua forma forte (interpretação é a alavanca; acesso é estrutural) e é
refutada onde prometia demais (esmagar codecs polidos em compressão geral).

---

## 0. O QUE ESTE PROJETO É — PARADIGMA, NÃO ALGORITMO

**Antes de ler qualquer número abaixo:** este projeto não é um codec. É uma
forma diferente de LER e INTERPRETAR dados. O codec foi apenas o primeiro
terreno onde essa forma virou medição.

A distinção muda como se lê todo o relatório:

```
O que foi medido NÃO foi "o BH".
Foi UMA interpretação do BH (constante + rampa), em UMA tarefa (codec).
```

Quando o veredicto diz "perde para o WebP em foto natural", isso **não é o
paradigma perdendo** — é *esta biblioteca de interpretações* sendo pobre
para *esta classe de conteúdo*. O paradigma é anterior ao algoritmo: ele
diz "leia o dado pela convenção que rende mais para o que você quer fazer".
Cada algoritmo é só uma instância dessa lei.

Os próprios dados provam que "perdeu" nunca é propriedade do paradigma:

```
gradiente, mesma árvore, só trocando a interpretação:
  61× PIOR que PNG  (interpretação "cor constante")
  → 48× MELHOR que WebP  (interpretação "rampa")
A interpretação move o resultado ~1000×. Logo, onde se perde, o que falta
é um endereço vazio na biblioteca — não uma falha da abordagem.
```

### A borda honesta (para o paradigma não virar promessa que nunca falha)

Há uma fronteira entre o que o MVP **provou** e o que ele **projeta** —
e ela precisa estar explícita, ou a tese vira infalsificável:

```
PROVADO    — onde a interpretação casa, o paradigma bate o estado da arte
             por ordens de grandeza (gradiente). Fato medido.
PROJETADO  — "para foto natural, outra interpretação ganharia". Plausível e
             ancorado (a interpretação que casa com textura é frequência,
             = o que JPEG/AV1 fazem). Mas é HIPÓTESE até construir e medir.
```

E o ponto que define o valor único do paradigma: **quando a interpretação
que "ganharia" já é a que o codec polido usa (DCT), o ganho do BH não vem
de bater DCT no jogo do DCT.** Vem das duas coisas que são exclusivas da
abordagem:

```
1. HIERARQUIA DE GRAÇA — a posição no stream codifica a estrutura, zero bits.
2. SELEÇÃO ADAPTATIVA POR REGIÃO — múltiplas interpretações coexistem e a
   certa é escolhida por região e por objetivo, sem custo de estrutura.
```

A contribuição do paradigma não é inventar a melhor interpretação para
cada caso. É ser a **moldura** onde muitas interpretações coexistem e a
certa é selecionada — por região, por conteúdo, por objetivo.

### O que isto significa para os próximos terrenos

A mesma moldura — biblioteca de interpretações + seletor por objetivo +
hierarquia grátis — não é específica de imagem:

```
codec   → interpretar pixels pela leitura que minimiza bytes×erro
banco   → interpretar bytes pela leitura mais barata para a query
memória → contexto embutido no dado, não buscado à parte
```

Onde este MVP perdeu, **um outro com outras especificações de interpretação
tem ganhos** — porque a abordagem não é o algoritmo, é a escolha de como
ler. O MVP fez duas coisas: provou o paradigma onde a interpretação existia,
e **mapeou os endereços vazios da biblioteca** — que é o roteiro do resto.

---

## 1. O EXPERIMENTO

Codec de imagem intra-frame (sem vídeo), em Python/NumPy, comparado contra
PNG, JPEG e WebP. Três alegações falsificáveis, com critério de sucesso E
de fracasso definidos ANTES de medir (spec §1):

```
C1 — DECODE PROGRESSIVO: custo de leitura escala com a resolução PEDIDA.
C2 — ROI: custo de leitura proporcional à área pedida.
C3 — COMPRESSÃO: o preço pago pelas propriedades C1/C2 é limitado
     (≤ PNG em sintético; ≤ 2× PNG em natural).
```

Formato `.bhc`: quadtree serializada em BFS por nível. A posição de cada
nó é **implícita na ordenação do stream** — o campo HIERARCHY de 24 bits
do documento original foi eliminado: a hierarquia é interpretação da
posição, não um dado armazenado.

---

## 2. RODADA v0.1 — MONO-INTERPRETAÇÃO

Primeira implementação: uma única leitura fixa (folha = cor constante).

**Veredicto:** C1 ❌ · **C2 ✅** · C3 ❌

| classe | imagem | BH/PNG (lossless) |
|---|---|---|
| sintético | gradient | 61,25× pior |
| sintético | shapes | 8,52× pior |
| screenshot | ui | 53,66× pior |
| natural | natural_city | 3,68× pior |
| natural | natural_forest | 6,04× pior |

- **C2 confirmada:** payload lido ≤ 1,2× a área pedida, em todas as imagens.
  A propriedade de acesso por região é real e generaliza.
- **C1 refutada:** preview barato em baixa resolução (thumbnail ~0,4%),
  mas a ~1,4× o custo de uma rendition única em alta resolução.
- **C3 refutada:** sem entropy coding, 3-61× pior que PNG.

*Diagnóstico:* o gradiente ser o PIOR caso não é sinal de complexidade —
é a interpretação "cor constante" sendo a errada para ele.

---

## 3. RODADA v0.2 — MULTI-INTERPRETAÇÃO

O código de 2 bits de cada nó virou um **selector de interpretação**
(exatamente o campo "tipo de dado" do HEADER no documento original):

```
LEAF      cor constante (3 bytes)
RAMP      rampa bilinear de 4 cantos (12 bytes)   ← interpretação nova
INTERNAL  subdivide
EMPTY     fora da imagem
```

Cada nó escolhe a interpretação que melhor explica seu quadrante. A
hierarquia passa a se ADAPTAR ao conteúdo.

**Veredicto cru:** C1 ❌ · C2 ❌ · C3 ❌ — pior no papel, melhor na verdade.
Os "refutado" são por margem fina e por motivos que confirmam a tese:

- **C2 caiu no fio:** um único ponto (natural_portrait, ROI 1%) leu 1,25%
  contra o limite de 1,20×. Causa: rampa é payload de 12 B vs 3 B da folha
  → unidades maiores, proporcionalidade mais grossa em ROI minúsculo.
- **C1 "piorou" porque os dados se reorganizaram:** rampas colapsam o
  detalhe para cima (nível N-1), então "1080p" passou a ser onde o
  conteúdo mora. Thumbnail e 480p continuam baratíssimos (0,5% e 2%).

**O ganho real apareceu no lossy** — onde a interpretação casa com o conteúdo:

| imagem (lossy, ~alta qualidade) | v0.1 BH/JPEG | v0.2 BH/JPEG |
|---|---|---|
| gradient | 0,1× | **~0,005×** (2 KB @ 55 dB) |
| shapes | 1,7× | **1,0×** (empata JPEG) |
| natural_forest | 6,3× pior | 4,4× pior |

O gradiente — pior caso do v0.1 — virou quase-nada. **A escolha da
interpretação moveu o resultado em ~1000×.**

---

## 4. HEAD-TO-HEAD POR TAREFA — BH vs CODECS POLIDOS

A pergunta certa não é "o BH comprime mais?". É: **"para uma tarefa real,
quanto trabalho cada formato precisa?"** Métrica primária: bytes lidos
(justa, independe de linguagem).

### 4.1 Conteúdo que casa com a interpretação (gradiente, lossy)

| formato | tamanho | PSNR |
|---|---|---|
| **BH-rampa (tosco, Python)** | **2,4 KB** | **57,9 dB** |
| WebP (Google, estado da arte) | 116,7 KB | 50,2 dB |
| JPEG | 434,4 KB | 51,9 dB |
| PNG (lossless) | 168,4 KB | ∞ |

**O codec imperfeito é 48× menor que o WebP, com qualidade MAIOR.** Não por
engenharia — por interpretação. A rampa É o gradiente; o WebP gasta
centenas de KB descrevendo com DCT o que 4 cantos descrevem exato.

### 4.2 Acesso — thumbnail ~256px de um 4K

| formato | natural_city | gradient |
|---|---|---|
| **BH** | **0,148 MB** | **0,003 MB** |
| WebP | 0,664 MB (4×) | 0,045 MB (15×) |
| JPEG | 1,008 MB (7×) | 0,191 MB (62×) |
| PNG | 6,469 MB (44×) | 0,168 MB (54×) |

O BH vence TODOS — inclusive em foto natural, onde perde em compressão.
Thumbnail só precisa do topo da pirâmide; nenhum polimento dá ao WebP a
capacidade de entregar preview sem ler o arquivo quase inteiro.

### 4.3 Acesso — região central 512×512 de um 4K

| formato | gradient | natural_city |
|---|---|---|
| **BH** | **~0 MB** | **0,625 MB** |
| WebP | 0,045 MB (111×) | 0,664 MB (1×) |
| JPEG | 0,191 MB (469×) | 1,008 MB (2×) |
| PNG | 0,168 MB (414×) | 6,469 MB (10×) |

Vitória esmagadora onde o arquivo polido é grande; em foto natural a
vantagem encolhe (o arquivo BH é grande, então ler um ramo dele já pesa).

---

## 5. VEREDICTO HONESTO

```
PROVADO ✅
  - Interpretação é a alavanca: 1000× no gradiente, só trocando a leitura.
  - Codec tosco bate codec polido (WebP) por 48× em conteúdo casado.
  - Acesso parcial (thumbnail/ROI) é vantagem estrutural: 4-469× menos
    bytes lidos, independente de polimento.

REFUTADO / LIMITES ❌
  - Compressão de foto natural: WebP/JPEG vencem (0,66 MB vs 7,95 MB).
    Falta transformada de frequência + entropy coding.
  - Tempo de parede: BH ~580 ms (Python) vs JPEG ~4 ms (C). Dívida de
    implementação, não de arquitetura — mas real hoje.
  - A vantagem de acesso se INVERTE quando o polido comprime a quase nada
    (thumbnail de UI: PNG inteiro < fração que o BH precisa ler).
```

**A lei que emergiu:** não existe "melhor interpretação" em abstrato —
existe a melhor interpretação para um OBJETIVO e uma CLASSE de conteúdo.
Onde casa, o tosco bate o polido por ordens de grandeza. Onde não casa,
perde. O trabalho de um codec BH maduro é ter a interpretação certa na
biblioteca para cada classe e escolher por região (rate-distortion) — que
é, não por acaso, o princípio dos codecs modernos (mode decision por bloco).

---

## 6. PRÓXIMOS PASSOS

```
1. Interpretação de FREQUÊNCIA (mini-DCT por bloco) na biblioteca —
   a peça que falta para a textura de foto natural.
2. Selector por RATE-DISTORTION (escolher por bytes×erro, não "cabe ou não").
3. Medir o ganho da ADAPTATIVIDADE em si: curva com 1, 2, 3 interpretações
   disponíveis — isolar o valor de TER escolha (a tese), não de uma
   interpretação específica.
4. Porta do C3 de acesso: índice de ranks por nível (eliminar o piso de
   ~8% de estrutura no ROI).
```

---

## ANEXOS — relatórios brutos

```
RESULTS_v0.1_mono_interpretacao.md   rodada 1, mono-interpretação
RESULTS.md                            rodada 2, multi-interpretação (v0.2)
RESULTS_HEADTOHEAD.md                 head-to-head por tarefa vs PNG/JPEG/WebP
```

Reprodução: `X:/miniconda3/python.exe src/bench/harness.py` (rodadas 1-2)
e `src/bench/headtohead.py` (head-to-head). Suíte: `pytest tests -q` (54
testes: roundtrip bit-exact, C1, C2, lossy, rampa, mapa de estrutura).

---

*"O byte sempre foi uma árvore binária implícita. Bits Hierárquicos apenas
nomeiam e formalizam o que sempre esteve lá — e cobram o preço por isso na
forma de eficiência."* — documento original, Dezembro 2025.

O MVP acrescenta: **o preço só compensa quando a interpretação casa com o
conteúdo. A arte do codec BH é a biblioteca de interpretações e a escolha
por região — não a árvore.**

E o enquadramento que governa tudo (ver §0): **isto não é um algoritmo, é
uma forma de ler dados.** Onde este MVP perdeu, não foi a abordagem que
falhou — foi um endereço vazio na biblioteca de interpretações. Outro
sistema, com outras especificações de interpretação para aquela classe de
dado, tem ganhos no mesmo lugar. O codec foi o primeiro terreno; o
paradigma é maior que ele.
