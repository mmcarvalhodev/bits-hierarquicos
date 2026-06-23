# BITS HIERÁRQUICOS — DOCUMENTO MASTER
## Uma forma diferente de ler dados — cinco terrenos, medidos, com as fronteiras marcadas

**Autor:** Márcio M. Carvalho
**Data:** Junho 2026
**Origem conceitual:** `arquitetura_bits_hierarquicos.md` (Dezembro 2025)
**Hardware de teste:** NVIDIA GeForce RTX 3060 12 GB · Python 3.13 · NumPy · CuPy/CUDA
**Estado:** 128 testes verdes · correção exata como portão antes de cada medição

> Este documento integra, num só lugar, todo o trabalho: a ideia, o método,
> os cinco terrenos (codec, banco de dados, verificação/Merkle, wafer, GPU),
> o mergulho completo na GPU real, as leis que emergiram, as fronteiras
> honestas e como reproduzir tudo. Os documentos por terreno (`*/RESULTS.md`)
> permanecem como detalhe bruto; este é a fonte única.

---

## ÍNDICE

1. A ideia em uma frase
2. O princípio, com cuidado
3. Por que não é "mais um algoritmo" — o método
4. Terreno 1 — Codec de imagem (ler para compactar)
5. Terreno 2 — Banco de dados (ler para consultar)
6. Terreno 3 — Verificação / Merkle (ler para provar)
7. Terreno 4 — Wafer (múltiplas camadas no mesmo dado)
8. Terreno 5 — GPU (movimento de dados, em silício real)
9. O mergulho GPU: processo e diagnóstico completo
10. As leis que emergiram
11. A tese-mãe — opcionalidade sob multiplicidade
12. O que isto NÃO é (honestidade)
13. Onde isto vale de verdade (aplicações + Amdahl)
14. Reprodução e índice de artefactos
15. Conclusão

---

## 1. A IDEIA EM UMA FRASE

```
Um dado não tem um significado fixo. Tem o significado que a convenção de
leitura lhe dá. A hierarquia — a estrutura — não está gravada nos bits;
está no acordo sobre como lê-los. Logo, ela pode custar zero, e os mesmos
bytes podem servir a muitos objetivos diferentes.
```

Ponto de partida (Dez/2025): **o byte já é uma árvore binária implícita.** A
letra 'a' (`01100001`) é oito bits soltos ou uma árvore por níveis — os bits
são os mesmos; muda a *interpretação*. Bits Hierárquicos tornam essa
interpretação explícita e a usam de propósito.

---

## 2. O PRINCÍPIO, COM CUIDADO

**(a) A hierarquia é grátis quando a posição a codifica.** Se os dados são
gravados numa ordem conhecida, a posição de cada elemento no fluxo já diz a
que nível/ramo ele pertence. Não se grava "nó 3 do nível 2" — deduz-se de
*onde* o byte está. Custo da estrutura: zero.

**(b) Os mesmos bytes, lidos por convenções diferentes, respondem perguntas
diferentes — sem transformação.** Se cada nó carrega um *resumo* do que está
abaixo (cor média, min/max, hash), então ler o topo dá resposta grosseira e
barata; ler um ramo dá resposta local; ler tudo dá a completa.

**(c) Não existe "melhor interpretação" em abstrato — só para um objetivo.** A
leitura para comprimir não é a de consultar nem a de provar. O valor é a
moldura onde várias interpretações coexistem, e escolher a que rende.

---

## 3. POR QUE NÃO É "MAIS UM ALGORITMO" — O MÉTODO

Um algoritmo resolve um problema; Bits Hierárquicos é anterior: uma *maneira
de ler* da qual muitos algoritmos nascem. A prova de generalidade exige mais
de um domínio — por isso a mesma moldura foi a **cinco terrenos que não
conversam**. Se rende nos cinco, é princípio, não truque.

Disciplina, em todos: **declarar antes de medir** onde deveria ganhar E
perder; depois medir, reportando os dois. Nenhum número prometido antes da
medição. **Correção exata é o portão** antes de qualquer comparação de
desempenho.

---

## 4. TERRENO 1 — CODEC DE IMAGEM (ler para compactar)

**A leitura:** quadtree — a imagem é dividida recursivamente; cada nó guarda
um resumo (cor média / cantos). Onde é uniforme, o ramo termina cedo.

**De graça:** thumbnail = ler o topo; ROI = ler um ramo; full = ler tudo. O
mesmo arquivo é todas as resoluções — a resolução é *quanto* dele se leu.

**Medido (head-to-head vs PNG/JPEG/WebP):**
- Conteúdo casado (gradiente, lossy): BH-rampa **2,4 KB @ 57,9 dB** vs WebP
  **116,7 KB @ 50,2 dB** → **48× menor, com qualidade maior.** A rampa *é* o
  gradiente; o WebP descreve-o com DCT.
- Acesso (thumbnail de foto natural 4K): BH **0,148 MB** vs WebP 0,664 (4×),
  JPEG 1,0 (7×), PNG 6,5 (44×). Ganha de todos, inclusive onde perde em
  compressão — porque preview não precisa do arquivo todo.

**A fronteira:** compressão de foto natural — os polidos vencem. A v0.3
adicionou interpretação DCT; trocar o critério de erro de L∞ para L2
destravou o DCT (cortou 40–66%), mas o gap não fechou: falta quantização +
entropy coding. **Quando preencher o vazio exige reconstruir o JPEG, o valor
único do BH volta a ser hierarquia grátis + acesso, não "comprime melhor".**

---

## 5. TERRENO 2 — BANCO DE DADOS (ler para consultar)

**A leitura:** árvore de agregação sobre tabela ordenada; cada nó guarda
min/max/soma/contagem. Análogo 1D da pirâmide do codec.

**Medido (1.000.000 de linhas, métrica = linhas lidas):**

| query | BH lê | plano lê | ganho |
|---|---|---|---|
| SUM global | **0** | 1.000.000 | ∞ (só a raiz) |
| SUM range 10% | 1.564 | 99.868 | **64×** |
| COUNT chave em 2% | 2.048 | 1.000.000 | **488×** |
| COUNT valor correlacionado > p99 | 92.736 | 1.000.000 | **11×** |
| valor independente / região / pouco seletivo | ~1.000.000 | 1.000.000 | **1–2× (fronteira)** |

**A perda vira ganho ao materializar a interpretação:** filtrar por região
(não agregada) lia tudo (1×); materializar um contador por região no nó →
leitura de raiz, **0 linhas (∞)**. Custo: armazenamento que escala com a
cardinalidade. Só vale p/ categórico de baixa cardinalidade. **É o "não se
indexa tudo" dos bancos reais — escolhe-se quais interpretações materializar.**

---

## 6. TERRENO 3 — VERIFICAÇÃO / MERKLE (ler para provar)

**A leitura:** a mesma árvore, mas o resumo do nó é um *hash* dos filhos —
uma árvore de Merkle (base de blockchain, git, Certificate Transparency).

**Medido (1.048.576 itens, métrica = bytes/nós):**

| tarefa | BH lê | baseline ingênuo | ganho |
|---|---|---|---|
| commitment de 1M itens | **32 B** (1 hash) | 33,5 MB | **1.048.576×** |
| prova de pertença | **644 B** (20 hashes) | 33,5 MB | **52.103×** |
| localizar adulteração | **40 nós** | 1.048.576 re-hashes | **26.214×** |

A prova cresce com **log n, não com n** (1k → 10 hashes; 1M → 20). A
multiprova partilha hashes-irmãos entre vários itens. **A fronteira:**
auditar tudo lê tudo; árvore ~2× de armazenamento; Merkle dá integridade,
**não sigilo** — cripto de confidencialidade é o oposto da tese (ciphertext
deve parecer ruído, sem estrutura explorável).

---

## 7. TERRENO 4 — WAFER (múltiplas camadas no mesmo dado)

**A ideia:** os mesmos bytes carregando camadas co-registradas (RGB +
profundidade + segmentação da mesma cena) sobre UMA hierarquia, lida por
lentes diferentes. **Teto de Shannon:** N bits carregam ≤ N bits — não há K
datasets de graça; partilha-se a *estrutura*, não o conteúdo.

**Medido — e a humildade que trouxe:** partilhar estrutura sozinho é alavanca
fraca (1,12× co-registrado; **perde** 0,32× desalinhado). Os levers reais,
que flipam a foto natural de perda para ganho:

```
união rígida ........................ 0,67× (perde)
+ luminância DERIVADA do RGB ........ 0,78×   (correlação = info mútua, Shannon-honesto)
+ REFINAMENTO local (não união) ..... 1,12×   (ganha)
```

Verificado com gate de reconstrução lossless (todas as camadas voltam
exatas). **Escopo honesto:** o 1,12× é vs guardar as camadas como árvores BH
independentes na MESMA qualidade — não contra um especialista (que em foto
natural ainda venceria o BH). O wafer torna eficiente guardar a *pilha
co-registrada* que hoje se grava replicada — o caso das aplicações de IA.

### Prova de escala — o filme (onde os levers compõem)

Tamanho espacial puro não muda a fração estrutura/payload (invariante de
escala). O que muda é o eixo de TEMPO. Proxy de 30s (720 frames, 3 camadas):

| estratégia | vs independente |
|---|---|
| independente | 1,00× |
| temporal (delta entre frames) | 1,65× |
| wafer (still) | 1,12× |
| **wafer + temporal** | **2,13×** |

Cadeia composta, medida: redundância temporal esvazia o payload → fração-
estrutura sobe de **16,7% → 33,4%** → e SÓ ENTÃO o wafer passa a valer. **O
filme é onde escala E redundância se somam.**

---

## 8. TERRENO 5 — GPU (movimento de dados, em silício real)

Fecha o laço com a motivação de Dez/2025 ("GPUs gastam 80-90% dos ciclos
movendo dados") — substituindo os 5-35× de hardware *fabricados* por medição
real na RTX 3060.

**Simulação (bytes movidos):** na carga agregação/LOD/contexto, o layout
hierárquico move **1.540× menos dados**. Mas contar bytes não é medir tempo.

**Teste real leve (CUDA events, 1 GB em VRAM):**

| tarefa | flat | BH | speedup | banda flat |
|---|---|---|---|---|
| redução total (1 GB) | 2.991 µs | 2,8 µs | 1.087× | 342 GB/s |
| agregação range 25% | 752 µs | 2,8 µs | 264× | 340 GB/s |

Três verdades: (1) ganho real e grande; (2) a razão de bytes (128 milhões×)
**exagera** — o BH O(1) bate no piso de lançamento de kernel (~2,8 µs); (3)
a premissa validou-se — flat a 342 GB/s, colado no teto de ~360 GB/s →
bandwidth-bound. (Detalhe e teste pesado: §9.)

---

## 9. O MERGULHO GPU: PROCESSO E DIAGNÓSTICO COMPLETO

### 9.1 Teste pesado — empurrar carga real

Array de 2 GB, **6.000 consultas** de agregação, kernel CUDA real no flat,
**3,51 TB** de tráfego. Fatiado em lançamentos curtos p/ não estourar o TDR
do Windows (kernel > 2 s é morto). Evidência de carga (`nvidia-smi dmon`):
SM a **100%**, ~106 W, memória 60-64%, 53→60 °C. Verificação flat vs BH:
erro relativo máx **4,0 × 10⁻¹⁰**.

| lado | tempo | nota |
|---|---|---|
| FLAT (meu kernel, 3,51 TB) | 26,3 s | 134 GB/s = **37% do teto** |
| FLAT ideal (banda pura, 360 GB/s) | 9,8 s | limite |
| BH (lê agregado) | ~6 ms (ruidoso) | + build único 86 ms |

### 9.2 As duas armadilhas de medição (o coração do diagnóstico)

O número bruto foi **4.725×** — e é enganoso:

1. **Kernel flat subótimo.** Sustentou 134 GB/s (37% do teto). O `dmon`
   mostrou SM 100% / memória 60% → limitado por ocupação, não banda. Parte do
   4.725× era o flat ser ruim. Contra um flat *ideal* (9,8 s): **~1.756×**.
2. **BH no piso de medição.** O tempo BH oscilou (6–123 ms) — perto do piso,
   o ruído domina; o multiplicador exato treme.

**Triangulação (métrica sem ruído = dados movidos):** flat move 3,51 TB; BH
move ~2 GB (build lê o array 1× + ~96 KB de consultas) → **~1.755×**. Dois
caminhos independentes (tempo-vs-ideal 1.756× e dados-movidos 1.755×)
convergem. **O número honesto é ~1.750×, não 4.725×.**

### 9.3 Escala para placas superiores

Extrapolação a partir da banda publicada (não medição; só a 3060 foi medida).

**Lote bandwidth-bound — razão INVARIANTE de hardware:**

| GPU | banda | flat (3,51 TB) | BH build (2 GB) | razão |
|---|---|---|---|---|
| RTX 3060 (medido) | 360 GB/s | 9,75 s | 5,6 ms | **1.755×** |
| RTX 4090 | 1.008 GB/s | 3,48 s | 2,0 ms | **1.755×** |
| H100 SXM | 3.350 GB/s | 1,05 s | 0,6 ms | **1.755×** |
| B200 | 8.000 GB/s | 0,44 s | 0,2 ms | **1.755×** |

Ambos escalam com a banda → razão constante. **Placa melhor = mesmo ganho
relativo, só mais rápido em absoluto. O ganho é algorítmico, portável.**

### 9.4 O piso é software: emulado vs nativo (no driver)

**Consulta única latency-bound:**

| GPU | flat (1 GB) | razão SW (emulado) | razão NATIVO (hipotético) |
|---|---|---|---|
| RTX 3060 | 2.778 µs | 992× | 9.259× |
| H100 | 299 µs | 107× | 995× |
| B200 | 125 µs | 45× | 417× |

Em software a razão single-shot ENCOLHE em placas melhores — porque o BH bate
no **piso de lançamento de kernel (~2,8 µs), que não é física**: é o custo de
lançar um kernel a partir do host. O tempo real de *ler* o agregado é a
latência de memória (~0,3 µs), ~10× menor. **É aqui que o "BH no driver" de
Dez/2025 importa:** nativo, o piso cairia ~10×, recuperando o ganho
single-shot. A coluna "NATIVO" é **hipotética/ilustrativa** (usa latência de
memória real para mostrar a direção; não mede silício que não existe).

Separação honesta:
```
NATIVO ajudaria → latency-bound (consulta única) + energia.
NATIVO NÃO muda → o lote bandwidth-bound (~1.750×): já é algorítmico, já roda
                  em software HOJE. A parte valiosa não precisa de driver.
```

### 9.5 Como o ~1.750× melhora em aplicações (o teto de Amdahl)

O ~1.750× é **por operação**. O ganho da APP é limitado pela fração `f` do
tempo gasto naquela operação:

```
speedup_app = 1 / ( (1-f) + f/1750 ) ≈ 1/(1-f)

   f = 50%  → ~2×      f = 90%  → ~10×
   f = 80%  → ~5×      f = 95%  → ~20×      f = 99%  → ~91×
```

Quem disser "1.750× na aplicação" ignora Amdahl. **Onde a forma aparece:**
OLAP/dashboards, séries temporais, geoespacial, data lakes (Parquet/zone-maps
já fazem — prova de campo), visualização LOD, atenção hierárquica em LLM
(direção de pesquisa). **Ganhos que não são ×velocidade:** latência →
interatividade (batch vira interativo), energia (não mover dados poupa
joules), throughput/custo (mais queries por GPU).

### 9.6 Modelo de hardware nativo (projeção a partir dos testes reais)

Para projetar o que um BH *no driver/controlador* daria, há um modelo
paramétrico onde cada entrada é rotulada **[MEDIDO]** (nossos testes),
**[PROJETADO]** (físico/publicado) ou **[ESPECULATIVO]** (silício que não
existe). Spec formal: `gpu/BH_NATIVE_HARDWARE_MODEL_SPEC.md`. Saídas:

| projeção | software (medido) | nativo (projetado) |
|---|---|---|
| latência consulta única (1 GB) | 1.044× | **9.747×** (piso = latência mem, não lançamento) |
| lote 6.000 consultas (3,51 TB) | 1.754× | **5.702×** (build folded near-memory) |
| energia (lote) | — | **~1.755× menos** (prop. aos dados movidos) |

A razão de energia (~1.755×) é robusta — depende só do *quociente de bytes
movidos*, que é [MEDIDO]; o valor absoluto em Joules é que é incerto. Tudo
isto é **projeção**, nunca "medimos em hardware nativo" — o silício não
existe. O modelo serve para dimensionar a oportunidade com honestidade, não
para reivindicá-la.

---

## 10. AS LEIS QUE EMERGIRAM

**Lei 1 — O ganho tem sempre a mesma origem.** O resumo mora nos nós (cor /
min-max / hash); ler seletivamente toca O(log n). Thumbnail, agregação e
commitment são *a mesma leitura*.

**Lei 2 — A fronteira tem sempre a mesma forma.** Quando a interpretação não
casa com o objetivo (textura natural, valor independente, auditoria total),
não há ganho. Não é falha — é um *endereço vazio na biblioteca*. Preenchê-lo
custa (armazenamento, ou reconstruir o estado da arte do domínio).

**Lei 3 — Uma estrutura, muitas leituras.** O valor não é vencer uma tarefa
(um especialista sempre vence uma só) — é servir muitas de uma estrutura. Só
compensa se as operações partilham a hierarquia E o ativo único é
competitivo. Opcionalidade é necessária, não suficiente.

**Lei 4 — O ganho precisa de estrutura-dominante.** Partilhar/ler estrutura
só move a agulha quando ela é fração grande do custo. Tamanho não basta;
precisa de *redundância* que esvazie o payload (o filme).

**Lei 5 — O ganho é algorítmico, não de hardware.** Vem de não-mover-dados.
Por isso é invariante de placa (lote) e portável; hardware nativo só ajuda o
regime latency-bound, não o limite algorítmico.

**Lei 6 — A hierarquia só rende quando a estrutura não é afogada pelo payload.**
O ganho do BH é proporcional à fração do custo que é ESTRUTURA. Onde o payload
domina, o ganho some — e isto reapareceu em TODOS os terrenos:
```
codec foto natural ... payload = pixels densos ........... perde
wafer ................ payload = valores por região ...... 1,12× (fraco)
multimodal ........... payload = embeddings 768-4096d ..... perde (d > ~96)
```
Onde a ESTRUTURA domina, o ganho sobrevive — e isto PREVÊ onde procurar:
dados esparsos, metadados, índices, telemetria, séries de escalares, logs,
grafos. NÃO tensores densos (pixels, embeddings). A Lei 6 é o mapa de onde a
vantagem mensurável pode existir — e onde não vale nem testar.

---

## 11. A TESE-MÃE — OPCIONALIDADE SOB MULTIPLICIDADE

Benchmark de portfólio — um ativo 4K servindo o mix {thumb, 480p, 1080p, 4K,
ROI}, BH (uma estrutura) vs especialistas:

```
gradient (casado)  BH 25,9× MENOR que a escada de renditions — ganha os dois eixos
ui / natural       BH PERDE — o WebP comprime cada peça melhor que um BH inchado
```

Lei medida: **ganho de portfólio = (operações partilham a hierarquia) × (o
ativo único é compressivamente competitivo).** A primeira quase sempre vale;
a segunda é o gargalo. Materializar entradas que ninguém ataca é sobrecarga
pura. A arte é escolher quais interpretações materializar.

---

## 12. O QUE ISTO NÃO É (HONESTIDADE)

```
NÃO bate especialistas numa tarefa isolada (JPEG/WebP em foto; B-tree em lookup).
NÃO viola Shannon (múltiplas leituras = projeções + estrutura, não capacidade).
NÃO inventa os domínios (AV1, Parquet, Merkle já existem) — a contribuição é a UNIFICAÇÃO.
NÃO é encriptação (confidencialidade exige ausência de estrutura).
NÃO é speedup universal de app (Amdahl: a app colhe 1/(1-f), não o ganho por-op).
NÃO é hardware BH-nativo (o testado é layout de software em GPU existente).
```

A indústria convergiu para hierarquia-com-resumo em campos isolados sem
perceber que era um só princípio. Nomear isso é o que transforma *"não é
algoritmo, é forma de ler"* de afirmação em demonstração triangulada.

---

## 13. ONDE ISTO VALE DE VERDADE (APLICAÇÕES)

Pelas Leis 3, 4 e 5, é a escolha certa quando o dado tem **muitos ângulos de
acesso** E **estrutura dominante (escala + redundância)** E é **reusado**:

- ativos grandes acedidos de muitas formas (filme 4K: resoluções + seek +
  preview + região, de UMA estrutura, sem escada de renditions);
- **pilhas co-registradas de IA** (RGB + profundidade + segmentação +
  embeddings da mesma cena) — a IA *gera* as camadas que tornam o wafer
  valioso;
- dados científicos/geoespaciais (bandas múltiplas, agregação + região);
- analytics/OLAP e séries temporais (agregação + range sobre dado reusado);
- integridade seletiva (provar um item sem revelar o resto).

**Não** é a escolha certa para: padrão de acesso único sobre conteúdo que um
especialista comprime bem; carga compute-bound; consulta sem reuso. Ali, o
especialista vence — e usá-lo é o certo.

---

## 14. REPRODUÇÃO E ÍNDICE DE ARTEFACTOS

```
codec    X:\bitH\        py -m pytest tests -q  (60)  src/bench/{harness,headtohead,portfolio,exp_dct_l2}.py
banco    X:\bitH\db\     py -m pytest tests -q  (26)  src/bench/harness.py
merkle   X:\bitH\merkle\ py -m pytest tests -q  (26)  src/bench/harness.py
wafer    X:\bitH\wafer\  py -m pytest tests -q  (7)   src/bench/{harness,film}.py
gpu      X:\bitH\gpu\    py -m pytest tests -q  (9)   src/bench/{harness,real_gpu,heavy_gpu,extrapolate}.py

Python: X:/miniconda3/python.exe  (NumPy, Pillow, hashlib, CuPy/CUDA)
128 testes verdes. Correção exata é o portão antes de qualquer medição.
Carga GPU visível por: nvidia-smi dmon -c 14 -s pucm  (durante o heavy_gpu.py)
```

Relatórios brutos (detalhe por trás de cada seção):
```
RESULTS_PARADIGMA_BH.md            síntese densa (tabelas)
RESULTS_MVP_BH_CODEC.md            codec (v0.1 → v0.2 → head-to-head)
RESULTS_PORTFOLIO.md               tese-mãe: portfólio vs especialistas
db/RESULTS.md                      banco (D1/D2/D3 + region_counts)
merkle/RESULTS.md                  Merkle (M1/M2/M3 + multiproof)
wafer/RESULTS.md  ·  RESULTS_FILME.md   wafer + prova de escala
gpu/RESULTS.md · RESULTS_REAL_GPU.md · RESULTS_HEAVY_GPU.md
gpu/PROCESSO_E_DIAGNOSTICO_GPU.md  diagnóstico GPU completo
```

---

## 15. CONCLUSÃO

O documento de Dezembro de 2025 abriu com a intuição certa — *"GPUs gastam o
tempo movendo dados; o byte sempre foi uma árvore implícita"* — e fechou com
números de hardware **fabricados** (5-35×). Cinco terrenos e dezenas de
medições depois, incluindo um teste real na RTX 3060 que fecha o laço na
própria motivação original, a forma forte e honesta da tese é esta:

> A árvore esteve sempre lá, em qualquer dado. O ganho não é um algoritmo
> esperto — é **escolher como ler o dado para o que se quer fazer**, e manter
> muitas leituras possíveis sobre a mesma estrutura. Esse ganho é real e por
> vezes esmagador (48× sobre o WebP no caso casado; 52.000× numa prova de
> Merkle; ∞ numa agregação; ~1.750× num lote de GPU real) — **mas só onde há
> muitas leituras a fazer, a estrutura domina o custo, e o dado é reusado.**
> Não em qualquer dado: exatamente onde isso vale.

A honestidade é metade do resultado. Saber onde o paradigma **perde** — foto
natural, padrão de acesso único, conteúdo independente, carga compute-bound,
e o teto de Amdahl no nível da aplicação — é o que torna confiável saber onde
ele **ganha**. Um PoC que só mostrasse vitórias seria propaganda. Este mostra
as duas faces, medidas, com a fronteira marcada em cada afirmação — e por
isso a tese sobrevive.

A diferença entre Dezembro de 2025 e este documento, numa linha: **um
prometia; este mede, e quando o número grande tinha gordura, tirou-a e
reportou o que resiste.**

---

*"Não é o algoritmo — é a forma de ler."*
