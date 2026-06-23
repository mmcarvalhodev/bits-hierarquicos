# PARADIGMA BITS HIERÁRQUICOS — RESULTADOS GERAIS
## Uma forma de ler dados, provada em três domínios sem relação entre si

**Autor:** Márcio M. Carvalho
**Data:** Junho 2026
**Origem:** `arquitetura_bits_hierarquicos.md` (Dezembro 2025)
**Status:** três PoCs medidos — codec, banco de dados, verificação (Merkle)

---

## A TESE

```
Isto não é um algoritmo. É uma forma diferente de LER e INTERPRETAR dados.

  - A hierarquia não está nos bits — está na CONVENÇÃO sobre como lê-los.
    A posição no stream codifica a estrutura. Custo: zero.
  - Os mesmos bytes, lidos por convenções diferentes, respondem operações
    diferentes SEM transformação.
  - Não existe "melhor interpretação" em abstrato — existe a melhor
    interpretação para um OBJETIVO. O ganho é o ato de escolher.
```

Para provar que isto é um paradigma e não um truque de um domínio, a mesma
moldura foi levada a **três terrenos que não se falam** — cada um testando
uma face diferente da leitura-por-objetivo:

```
1. CODEC  → ler para COMPACTAR   (a interpretação casa com o CONTEÚDO)
2. BANCO  → ler para CONSULTAR   (a interpretação casa com a QUERY)
3. MERKLE → ler para VERIFICAR   (a interpretação casa com a PROVA)
```

A mesma estrutura, três objetivos. Os três deram o mesmo veredicto
estrutural — e a mesma fronteira.

---

## O RESULTADO EM UMA TABELA

| | objetivo | nó carrega | "thumbnail" (lê o topo) | "ROI" (lê um ramo) | a fronteira (não casa) |
|---|---|---|---|---|---|
| **CODEC** | compactar | cor média / cantos | preview: 0,4–1% do arquivo | região ∝ área | textura natural |
| **BANCO** | consultar | min/max/sum/count | agregado global: 0 linhas | filtro poda ∝ seletividade | valor independente da chave |
| **MERKLE** | verificar | hash dos filhos | commitment: 1 hash | prova: log n hashes | auditar tudo |

A mesma frase descreve os três: **onde a interpretação casa com o objetivo,
a hierarquia grátis dá ganhos de ordens de grandeza; onde não casa, perde —
e o "não casa" é sempre um endereço vazio na biblioteca, nunca um defeito
da abordagem.**

---

## TERRENO 1 — CODEC (compactar)

A interpretação como alavanca, medida em frames 4K reais:

```
Mesmos pixels (gradiente), só trocando a convenção de leitura:
  61× PIOR que PNG   (interpretação "cor constante")
  → 48× MELHOR que WebP, com qualidade maior   (interpretação "rampa")
Movimento de ~1000×, zero mudança no algoritmo de árvore.
```

**Head-to-head vs codecs polidos** (métrica: bytes para a tarefa):

| tarefa | BH | melhor polido | resultado |
|---|---|---|---|
| gradiente lossy (conteúdo casado) | 2,4 KB @ 57,9 dB | WebP 116,7 KB @ 50,2 dB | **48× menor, +qualidade** |
| thumbnail de foto natural 4K | 0,148 MB | WebP 0,664 MB | **4× menos** (7× vs JPEG, 44× vs PNG) |
| compressão de foto natural | 7,95 MB | WebP 0,66 MB | **PERDE** (a fronteira) |

Veredicto: ganha por construção em acesso e em conteúdo casado; perde em
compressão de foto natural. Detalhe completo em `RESULTS_MVP_BH_CODEC.md`.

### Codec v0.3 — DCT e o limite da métrica (onde a fronteira foi dissecada)

Foto natural era o "endereço vazio" do codec. Tentou-se preenchê-lo
adicionando a interpretação de frequência (mini-DCT) e medindo. O achado
delimita a fronteira com precisão cirúrgica — e mostra que ela tinha TRÊS
camadas, não uma:

```
1. A interpretação (DCT)              → adicionada (seletor por rate-distortion)
2. A métrica que a seleciona (L2)     → o gargalo real, provado por experimento
3. Quantização + entropy coding       → ainda ausente = reconstruir o JPEG
```

**Camada 2, o achado central:** o seletor media distorção como erro-MÁXIMO
por nó (L∞). Esse critério favorece constante/rampa (que garantem erro
máximo) e MATA o DCT (que troca erro máximo por erro médio). Com L∞, o DCT
nem disparava em metade dos casos:

| foto (thr) | L∞: tamanho @ PSNR (nós DCT) | L2: tamanho @ PSNR (nós DCT) |
|---|---|---|
| city (16) | 2,78 MB @ 36,0 dB (**0 DCT**) | 1,03 MB @ 31,1 dB (8.776 DCT) |
| city (24) | 1,60 MB @ 32,9 dB (**0 DCT**) | 0,54 MB @ 29,1 dB (4.363 DCT) |
| forest (8) | 0,98 MB @ 41,4 dB (2.803) | 0,59 MB @ 39,8 dB (3.401) |

Trocar L∞ por L2 (RMSE) destravou o DCT e cortou o arquivo **40–66%**. A
seleção de interpretação FUNCIONA — o DCT passou a competir por nós e a
vencê-los onde casa.

**Mas o gap com o WebP não fechou** (ficou 2,8–15× conforme o ponto de
operação), porque a camada 3 falta: o nó DCT guarda 48 coeficientes int16
CRUS (96 B), enquanto o WebP quantiza e entropy-codifica os mesmos
coeficientes numa fração disso.

**A lição que amarra a trilogia:** quando preencher o endereço vazio exige
reimplementar o estado da arte do domínio (quantização+entropia = o JPEG),
a contribuição única do BH deixa de ser "comprime melhor" e volta a ser o
que sempre foi — *hierarquia grátis + seleção adaptativa de interpretação*.
O paradigma rende onde o ganho vem da ESTRUTURA DE LEITURA (acesso,
consulta, prova); não rende onde o ganho viria de ESPREMER BITS DE UM SINAL
(quantização/entropia) — um problema ortogonal que toda interpretação
herda igual. A fronteira de foto natural não é falta de interpretação: é
compressão de coeficiente, que está fora do que o paradigma reivindica.

(Engenharia do DCT + seletor rate-distortion: contribuição externa. Métrica
L∞→L2 dissecada em `src/bench/exp_dct_l2.py`.)

---

## TERRENO 2 — BANCO DE DADOS (consultar)

Árvore de agregação sobre 1.000.000 de linhas (métrica: linhas lidas):

| query | BH lê | plano lê | ganho |
|---|---|---|---|
| SUM global | **0** | 1.000.000 | ∞ (só a raiz) |
| SUM range 10% | 1.564 | 99.868 | **64×** |
| COUNT chave em 2% | 2.048 | 1.000.000 | **488×** |
| COUNT valor correlacionado > p99 | 92.736 | 1.000.000 | **11×** |
| valor independente / região / pouco seletivo (D3) | ~1.000.000 | 1.000.000 | **1–2× (a fronteira)** |

Veredicto: D1 (agregação) e D2 (poda) confirmadas; D3 (eixo errado /
seletividade baixa) é a fronteira — a mesma do codec. Detalhe em
`db/RESULTS.md`.

### A perda vira ganho ao materializar a interpretação (custo: armazenamento)

O filtro por região era a perda D3 (lê tudo, 1×). Materializar um contador
por região em cada nó (`region_counts`) transformou a MESMA query numa
leitura de raiz:

| query | BH lê | ganho |
|---|---|---|
| `COUNT region==3` por poda min/max | 1.000.000 | 1× (a perda) |
| `COUNT region==3` com `region_counts` no nó | **0** | ∞ |

É a confirmação direta de "preencher o endereço vazio da biblioteca". Mas
não é grátis: cada interpretação materializada custa armazenamento (aqui
~64 B/nó) e **só escala para categóricos de baixa cardinalidade** — com
milhões de valores distintos seria proibitivo. A fronteira não desaparece;
muda de endereço. É a mesma lógica de "não se indexa tudo" dos bancos reais.

---

## TERRENO 3 — VERIFICAÇÃO / MERKLE (provar)

Árvore de Merkle sobre 1.048.576 itens (métrica: bytes/nós para a tarefa):

| tarefa | BH lê | baseline ingênuo | ganho |
|---|---|---|---|
| Commitment de 1M itens | **32 B** (1 hash) | 33,5 MB | **1.048.576×** |
| Prova de pertença | **644 B** (20 hashes) | 33,5 MB | **52.103×** |
| Localizar adulteração | **40 nós** | 1.048.576 re-hashes | **26.214×** |

A prova cresce com **log n, não com n**: 1k itens → 10 hashes; 1M → 20.
Veredicto: M1/M2/M3 confirmadas; a fronteira (auditar tudo lê tudo;
~2× armazenamento; integridade ≠ sigilo) declarada. Detalhe em
`merkle/RESULTS.md`.

**Nota de honestidade sobre cripto:** confidencialidade (cifrar p/ esconder)
é PÉSSIMO encaixe — ciphertext deve ser indistinguível de ruído; estrutura
interpretável = cifra quebrada. Não foi construído. O encaixe é INTEGRIDADE
(Merkle), onde o agregado do nó é um hash.

---

## TERRENO 4 — WAFER (múltiplas camadas no mesmo dado gravado)

A forma mais radical da tese: os mesmos bytes carregando MÚLTIPLAS camadas
co-registradas (RGB + profundidade + segmentação da mesma cena) sobre UMA
hierarquia, lida por lentes diferentes. O teto é Shannon: N bits carregam
≤ N bits — não há K datasets de graça. O que se partilha é a ESTRUTURA, não
o conteúdo.

| cenário | wafer vs K arquivos | leitura |
|---|---|---|
| co-registrado (mesma partição) | **1,12×** | estrutura amortizada ~4×, mas é só 3,7% do total |
| desalinhado (partições independentes) | **0,32× (perde)** | união super-subdivide |
| foto + luminância + segmentação | **0,67× (perde)** | bordas não alinham sob threshold |

**Achado central:** partilhar estrutura sozinho é alavanca FRACA — a
estrutura é fração mínima quando o payload domina. Os levers que de facto
viram o jogo são dois, e juntos flipam a foto natural de perda para ganho:

```
C   união rígida ........................... 0,67× (perde)
C+  + luminância DERIVADA do RGB ............ 0,78× (correlação = info mútua, Shannon-honesto)
C++ + REFINAMENTO local (não união) ........ 1,12× (GANHA)
```

- **Correlação entre-camadas (W4):** gravar a camada 2..K como predição da 1
  partilha a *informação mútua*, não conteúdo independente. Derivar
  luminância do RGB poupou 176 KB.
- **Base + refinamento local (W5):** em vez da união rígida (onde a
  segmentação arrastava a árvore RGB a super-subdividir), uma árvore base
  partilhada + mini-quadtree local por camada. A segmentação refina só onde
  precisa, sem arrastar as outras. Isto fecha a fronteira do desalinhamento.

Verificado: `reconstruct_with_refinements` reconstrói **todas** as camadas
exatas (gate de correção lossless antes de medir). Escopo honesto: o 1,12×
é wafer-BH vs BH-independente na MESMA qualidade — não contra um especialista
(que, em foto natural, ainda venceria o BH). Detalhe em `wafer/RESULTS.md`.

### Prova de escala — o filme (onde os levers compõem)

Tamanho espacial puro NÃO muda a fração estrutura/payload (é invariante de
escala, ~1/9 para RGB). O que muda tudo é o eixo de TEMPO. Proxy de 30s
(720 frames, 3 camadas co-registradas):

| estratégia | vs independente |
|---|---|
| independente | 1,00× |
| temporal (delta entre frames) | 1,65× |
| wafer (still, sem temporal) | 1,12× |
| **wafer + temporal** | **2,13×** |

A cadeia composta, medida: a redundância temporal esvazia o payload → a
fração-estrutura sobe de **16,7% → 33,4%** → e SÓ ENTÃO o wafer passa a
valer (ganho 1,12×→1,29× sobre o temporal). **O filme é onde escala E
redundância se somam.** Uma foto não tem nenhuma das duas; por isso o wafer
mede fraco nela. Detalhe em `wafer/RESULTS_FILME.md`.

---

## TERRENO 5 — GPU (movimento de dados, em silício real)

Fecha o laço com a motivação original (Dez/2025: "GPUs gastam 80-90% dos
ciclos movendo dados") — e substitui os 5-35× de hardware FABRICADOS de lá
por medição real numa RTX 3060.

**Simulação (contagem de bytes movidos da DRAM, carga agregação/LOD/contexto):**
o layout hierárquico move **1.540×** menos dados no total da carga. Detalhe
em `gpu/RESULTS.md`.

**Teste REAL (CUDA events na RTX 3060, 1 GB em VRAM):**

| tarefa | tempo flat | tempo BH | speedup REAL | razão de bytes | banda flat |
|---|---|---|---|---|---|
| redução total (1 GB) | 2.991 µs | 2,8 µs | **1.087×** | 128.000.000× | 342 GB/s |
| agregação range 25% | 752 µs | 2,8 µs | **264×** | 16.000.000× | 340 GB/s |

As três verdades que só o hardware deu:
1. **O ganho é real e enorme** — 264–1.087× de tempo de parede, não simulado.
2. **A razão de bytes exagera por ~100.000×** — a leitura BH O(1) bate no
   PISO de lançamento de kernel (~2,8 µs fixos), que a simulação não modela.
3. **A premissa validou-se** — o flat rodou a 342 GB/s, colado no teto de
   ~360 GB/s da 3060: é genuinamente bandwidth-bound, logo a ponte
   bytes→tempo é legítima e o ganho não é artefato.

Fronteira: build do agregado custa ~15 ms uma vez (amortiza em ~5 consultas;
p/ consulta única o flat ganha); vale só bandwidth-bound; é BH como layout de
software, NÃO o hardware BH-nativo (que não existe). Detalhe em
`gpu/RESULTS_REAL_GPU.md`.

**Teste PESADO (carga real, lote de 6.000 consultas, 3,51 TB varridos):** a
3060 foi empurrada por 26 s a 100% de SM (confirmado por `nvidia-smi dmon`).
Aqui duas armadilhas de medição foram diagnosticadas e corrigidas:
1. **kernel flat subótimo** — sustentou só 134 GB/s (37% do teto); um bloco
   por consulta é limitado por ocupação, não banda. Contra um flat *ideal*
   (360 GB/s) o ganho cai de 4.725× para **~1.750×**.
2. **lado BH no piso de medição** — o tempo BH oscila (6–120 ms), então o
   multiplicador exato treme.

O número que sobrevive aos dois caminhos independentes (tempo-vs-flat-ideal
E dados-movidos: flat 3,51 TB vs BH ~2 GB incluindo o build) é **~1.750×**.
Esse é o valor honesto do lote pesado. Detalhe em `gpu/RESULTS_HEAVY_GPU.md`
e no diagnóstico `gpu/PROCESSO_E_DIAGNOSTICO_GPU.md`.

**A diferença entre Dez/2025 e agora:** o doc prometia "5-35× de hardware"
sem medir; este mede — e quando o número grande (4.725×) tinha gordura
(kernel ruim + ruído de piso), nós a tiramos e reportamos o ~1.750× que
resiste. Um prometia; este mede e marca a fronteira.

---

## A TESE-MÃE — OPCIONALIDADE SOB MULTIPLICIDADE

O valor do BH não é vencer UMA tarefa (um especialista sempre vence uma só:
JPEG na compressão, B-tree no lookup). É oferecer MÚLTIPLAS entradas de
ataque sobre UMA estrutura, e escolher o ângulo que ganha por operação.

Benchmark de portfólio — um ativo 4K servindo o mix {thumb, 480p, 1080p,
4K, ROI}, BH (uma estrutura) vs especialistas:

```
gradient (casado)   BH 25,9× MENOR que a escada de renditions — ganha os dois eixos
ui / natural        BH PERDE — o WebP comprime cada peça melhor que um BH inchado
```

A lei medida: **ganho de portfólio = (operações partilham a MESMA
hierarquia) × (o ativo único é compressivamente competitivo).** A primeira
condição quase sempre vale; a segunda é o gargalo. Opcionalidade é
NECESSÁRIA mas não SUFICIENTE — e materializar entradas que ninguém ataca é
sobrecarga pura. A arte é escolher quais interpretações materializar.
Detalhe em `RESULTS_PORTFOLIO.md`.

---

## O QUE OS CINCO, JUNTOS, PROVAM

```
1. O GANHO TEM SEMPRE A MESMA ORIGEM
   O agregado mora nos nós (cor média / min-max / hash); ler seletivamente
   toca O(log n). Thumbnail, agregação e commitment são a MESMA leitura.

2. A FRONTEIRA TEM SEMPRE A MESMA FORMA
   Quando a interpretação não casa com o objetivo — textura natural, valor
   independente da chave, auditoria total — não há ganho. Não é falha do
   paradigma: é um endereço vazio na biblioteca de interpretações.

3. A MESMA ESTRUTURA SERVE VÁRIAS LEITURAS, SEM ÍNDICES SEPARADOS
   codec:  thumbnail / ROI / decode full
   banco:  agregado / poda / scan cru / categórico
   merkle: commitment / prova / multiprova / localização / auditoria
   wafer:  K camadas co-registradas sobre uma hierarquia
   Uma estrutura; a leitura é escolhida pelo objetivo da query.

4. O GANHO PRECISA DE ESTRUTURA-DOMINANTE
   Partilhar/ler estrutura só compensa quando ela é fração grande do custo.
   No filme, a redundância temporal esvazia o payload e a estrutura passa a
   dominar — aí os ganhos compõem. Escala + redundância, não só tamanho.
```

**A honestidade que mantém isto verdadeiro:** nenhum dos três inventa seu
domínio. Codecs já fazem mode-decision por bloco (AV1); bancos já têm
zone-maps (Parquet); Merkle é base de blockchain/git/Certificate
Transparency. O que é original **não é a engenharia — é a unificação**:
mostrar que decode progressivo de imagem, poda de agregação em banco e
prova de Merkle são *a mesma leitura-por-objetivo-sobre-hierarquia-grátis*.

A indústria convergiu para hierarquia-com-resumo em três campos isolados,
sem perceber que era o mesmo princípio. O paradigma BH nomeia esse
princípio — e isso é o que transforma *"não é um algoritmo, é uma forma de
ler dados"* de afirmação em demonstração triangulada.

---

## ESTADO E REPRODUÇÃO

```
codec   X:\bitH\               py -m pytest tests -q   (60 testes, c/ DCT v0.3)
                               src/bench/harness.py + headtohead.py + portfolio.py + exp_dct_l2.py
banco   X:\bitH\db\            py -m pytest tests -q   (26 testes, c/ region_counts)
                               src/bench/harness.py
merkle  X:\bitH\merkle\        py -m pytest tests -q   (26 testes, c/ multiproof)
                               src/bench/harness.py
wafer   X:\bitH\wafer\         py -m pytest tests -q   (7 testes, c/ refinamento)
                               src/bench/harness.py + film.py
gpu     X:\bitH\gpu\           py -m pytest tests -q   (9 testes)
                               src/bench/harness.py (sim) + real_gpu.py (RTX 3060)

Python: X:/miniconda3/python.exe   (NumPy, Pillow, hashlib, CuPy/CUDA)
128 testes verdes; correção exata como gate antes de qualquer medição.
```

Relatórios brutos por terreno:
```
RESULTS_MVP_BH_CODEC.md   codec consolidado (v0.1 → v0.2 → head-to-head)
RESULTS_PORTFOLIO.md      tese-mãe: portfólio vs especialistas
db/RESULTS.md             banco de dados (D1/D2/D3 + region_counts)
merkle/RESULTS.md         verificação / Merkle (M1/M2/M3 + multiproof)
wafer/RESULTS.md          wafer: estrutura vs correlação
wafer/RESULTS_FILME.md    prova de escala: o filme (escala + redundância)
gpu/RESULTS.md            simulação de movimento de dados (bytes)
gpu/RESULTS_REAL_GPU.md   teste REAL na RTX 3060 (tempo de parede)
```

---

*"O byte sempre foi uma árvore binária implícita."* — Dezembro 2025.
Cinco terrenos depois — incluindo o teste real na GPU que fecha o laço com a
motivação original —, a forma forte da tese: **a árvore estava sempre lá,
em qualquer dado; o ganho é escolher como lê-la para o que se quer fazer.
Não é o algoritmo — é a forma de ler. E o ganho é maior onde há muitas
leituras a fazer (opcionalidade) e onde a estrutura domina o custo (escala
+ redundância) — não em qualquer dado, mas exatamente onde isso vale.**
