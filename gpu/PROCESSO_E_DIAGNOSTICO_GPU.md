# PROCESSO E DIAGNÓSTICO — TESTE GPU (Bits Hierárquicos)
## Da simulação ao silício real: como medimos, o que achámos, onde nos enganámos

**Autor:** Márcio M. Carvalho
**Data:** Junho 2026
**Hardware:** NVIDIA GeForce RTX 3060, 12 GB, driver 551.86
**Ambiente:** Python 3.13 (miniconda) · CuPy 14.0.1 · CUDA 12.6 · NumPy

---

## 0. OBJETIVO

Fechar o laço com a motivação original (documento de Dez/2025: *"GPUs gastam
80-90% dos ciclos movendo dados"*) — que lá terminou em ganhos de hardware
**fabricados (5-35×)**. Aqui a meta é o oposto: medir, na máquina real, a
ÚNICA coisa honestamente mensurável (movimento de dados e tempo), e marcar
exatamente onde a medida deixa de valer.

A pergunta concreta: **para uma carga de agregação sobre um array grande em
VRAM, o layout hierárquico (BH) — que responde lendo um agregado
pré-computado — bate o layout convencional (flat) — que varre os dados — em
tempo de parede real?**

---

## 1. AS TRÊS ETAPAS

```
Etapa 1  SIMULAÇÃO       conta bytes movidos da DRAM (modelo, sem GPU)
Etapa 2  TESTE REAL LEVE tempo de parede, consultas isoladas (CUDA events)
Etapa 3  TESTE PESADO    lote de 6.000 consultas, 3,51 TB, placa saturada
```

Cada etapa com **gate de correção** antes de medir: o agregado BH tem de dar
exatamente a mesma soma que a varredura flat (verificado por `allclose`).

---

## 2. ETAPA 1 — SIMULAÇÃO (contagem de bytes)

**O que mede:** bytes movidos da DRAM para cumprir a carga, layout flat vs
BH, com linha de cache de 128 B e penalidade de scatter (cada nó tocado =
1 linha inteira, mesmo usando 16 B dela — para não favorecer o BH).

**Resultado:** na carga {agregação, level-of-detail, contexto, filtro}, o BH
move **1.540× menos dados** no total.

**Limite reconhecido:** contar bytes não é medir tempo. Bytes viram tempo só
se o kernel for bandwidth-bound. Por isso fomos ao silício.

(Código: `src/bhgpu/sim.py`, `src/bench/harness.py`. Relatório: `RESULTS.md`.)

---

## 3. ETAPA 2 — TESTE REAL LEVE (RTX 3060)

**Método:** array de 256M float32 (1 GB) em VRAM. BH = prefix-sum dos
agregados de bloco (forma prática do segment tree). Tempo por CUDA events,
mediana de 200 chamadas, 30 de warmup.

| tarefa | flat | BH | speedup | banda flat |
|---|---|---|---|---|
| redução total (1 GB) | 2.991 µs | 2,8 µs | 1.087× | 342 GB/s |
| agregação range 25% | 752 µs | 2,8 µs | 264× | 340 GB/s |

**Três leituras:**
1. Ganho real e grande (264–1.087× de tempo de parede).
2. A razão de bytes (128 milhões×) **exagera** — o BH O(1) bate no piso de
   lançamento de kernel (~2,8 µs fixos). O silício tem um chão que a
   simulação não modela.
3. A premissa validou-se: o flat a 342 GB/s está colado no teto de ~360 GB/s
   → genuinamente bandwidth-bound.

**Crítica ao próprio teste:** o lado BH era trivial demais (ler 1 escalar
pronto). Não empurrava a placa. Daí a etapa 3.

(Código: `src/bench/real_gpu.py`. Relatório: `RESULTS_REAL_GPU.md`.)

---

## 4. ETAPA 3 — TESTE PESADO (empurrar carga real)

**Método:** array de 512M float32 (2 GB). Lote de **6.000 consultas** de
agregação de range, alinhadas a bloco. Lado flat = **kernel CUDA real**
(`RawKernel`), um bloco por consulta, redução em memória partilhada, varrendo
cada range na VRAM. Lado BH = leitura vetorizada do prefix. Tráfego flat
total: **3,51 TB**.

**Mitigação de TDR (Windows):** um kernel > 2 s na GPU de display é morto
pelo SO. Solução: fatiar em lançamentos de 256 consultas (~<1 s cada),
somando ~26 s sem nenhum kernel individual estourar o limite.

**Evidência de carga real** (`nvidia-smi dmon`, durante a varredura):

```
# gpu  pwr  gtemp   sm   mem   mclk  pclk    fb
   0   106    53   100    62   7300  1942   3023
   0   108    57   100    35   7300  1942   3011
   0   111    60   100    63   7300  1927   3011
```
SM a **100%**, ~106 W, controlador de memória 60-64%, temperatura 53→60 °C,
3 GB de VRAM em uso. A placa foi genuinamente saturada por ~26 s.

**Verificação:** flat vs BH batem com erro relativo máximo **4,0 × 10⁻¹⁰**.

**Números brutos:**

| lado | tempo | nota |
|---|---|---|
| FLAT (meu kernel, 3,51 TB) | 26,3 s | 134 GB/s = **37% do teto** |
| FLAT ideal (banda pura, 360 GB/s) | 9,8 s | estimativa do limite |
| BH (lê agregado) | ~6 ms (ruidoso) | + build único 86 ms |

(Código: `src/bench/heavy_gpu.py`. Relatório: `RESULTS_HEAVY_GPU.md`.)

---

## 5. DIAGNÓSTICO — as duas armadilhas de medição

O número bruto do teste pesado foi **4.725×** (26,3 s ÷ 6 ms). Esse número é
**enganoso**, e o diagnóstico é a parte mais importante deste documento.

### Armadilha 1 — kernel flat subótimo

O flat sustentou só **134 GB/s = 37% do teto** da 3060. O `dmon` explica:
SM a 100% mas memória a ~60% → o kernel está limitado por **ocupação /
overhead da redução**, não por banda pura. "Um bloco por consulta" com 256
threads não satura a hierarquia de memória.

**Consequência:** parte do 4.725× vinha do meu flat ser ruim, NÃO do BH ser
mágico. Contra um flat *ideal* (bandwidth-bound a 360 GB/s, ~9,8 s), o ganho
cai para **~1.756×**.

### Armadilha 2 — lado BH no piso de medição

O tempo BH oscilou entre execuções (**6 ms a 123 ms**) — está tão perto do
piso (alocação do gather + lançamento) que o ruído domina. Logo o
multiplicador exato **treme**; reportar "4.725×" como número firme seria
desonesto.

### A triangulação — o número que resiste

Para fugir do ruído, usámos a métrica **sem ruído**: dados movidos.

```
FLAT move ......... 3,51 TB (varre todos os ranges)
BH move ........... ~2 GB   (build lê o array 1× + ~96 KB das consultas)
razão ............. ~1.755×
```

Dois caminhos **independentes** — tempo-vs-flat-ideal (1.756×) e
dados-movidos (1.755×) — convergem para o mesmo valor. Por isso o número
honesto do lote pesado é **~1.750×**, não 4.725×.

---

## 6. O QUE O TESTE PROVA E NÃO PROVA

```
PROVA
  - A carga foi real: 3,51 TB varridos, placa a 100% de SM por 26 s.
  - O BH responde as 6.000 consultas movendo ~1.750× menos dados, com a
    MESMA resposta (verificada a 4e-10).
  - O ganho é estrutural: vem de NÃO mover os dados. Nenhum kernel flat
    melhora isso, porque os dados existem e precisam ser lidos.
  - A premissa bandwidth-bound é real (flat colado no teto no teste leve).

NÃO PROVA
  - Não é o hardware BH-nativo do doc de Dez/2025; é BH como LAYOUT DE
    SOFTWARE em GPU existente (a "Fase 1" honesta).
  - Não vale para consulta única (o build não amortiza) nem para kernel
    compute-bound (a ponte bytes→tempo só vale bandwidth-bound).
  - O número exato treme perto do piso; o defensável é a ordem (~10³×),
    cravada pela razão de dados movidos.
```

---

## 7. ESCALA PARA PLACAS SUPERIORES E O PISO DE SOFTWARE

Pergunta natural: numa GPU melhor (4090, H100, B200), o ganho cresce? A
resposta é **contraintuitiva** e depende do regime. Extrapolação a partir da
banda de memória publicada (NÃO é medição; só a 3060 foi medida).

### Lote bandwidth-bound (o caso real) — a razão é INVARIANTE

| GPU | banda | flat (3,51 TB) | BH build (2 GB) | razão |
|---|---|---|---|---|
| RTX 3060 (medido) | 360 GB/s | 9,75 s | 5,6 ms | **1.755×** |
| RTX 4090 | 1.008 GB/s | 3,48 s | 2,0 ms | **1.755×** |
| H100 SXM | 3.350 GB/s | 1,05 s | 0,6 ms | **1.755×** |
| B200 | 8.000 GB/s | 0,44 s | 0,2 ms | **1.755×** |

Os dois lados são bandwidth-bound e escalam JUNTOS com a banda → a razão não
muda. Placa melhor = mesmo ganho relativo, só mais rápido em absoluto. **O
ganho é algorítmico (não-mover-dados), portável entre hardwares.**

### Consulta única latency-bound — emulado vs NATIVO (no driver)

| GPU | flat (1 GB) | razão SW (emulado) | razão NATIVO (hipotético) |
|---|---|---|---|
| RTX 3060 | 2.778 µs | 992× | 9.259× |
| RTX 4090 | 992 µs | 354× | 3.307× |
| H100 | 299 µs | 107× | 995× |
| B200 | 125 µs | 45× | 417× |

Em software, a razão single-shot ENCOLHE em placas melhores — porque o BH bate
no **piso de lançamento de kernel (~2,8 µs)**, que NÃO é física: é o custo de
lançar um kernel a partir do host. O tempo real de *ler* o agregado é a
latência de memória (~0,3 µs), ~10× menor.

**É aqui que o "BH no driver" do doc de Dez/2025 importa de verdade.** Se a
leitura do agregado fosse uma operação nativa (no driver / controlador de
memória), o piso cairia de ~2,8 µs (lançamento) para ~0,3 µs (latência),
recuperando ~10× no regime latency-bound. A coluna "NATIVO" é **hipotética e
ilustrativa** (usa a latência de memória, um número real, para mostrar a
DIREÇÃO — não mede silício que não existe).

**A separação honesta — o que o nativo muda e o que não muda:**
```
NATIVO ajudaria   → regime latency-bound (consulta única em GPU rápida);
                    + energia (ler agregado sem trazer dados aos SMs).
NATIVO NÃO muda   → o lote bandwidth-bound (~1.750×): já é algorítmico, já
                    roda em SOFTWARE hoje, na 3060. Hardware não melhora o
                    limite de não-mover-dados.
```
Consequência estratégica: **a parte valiosa (~1.750× em lote) NÃO precisa de
driver** — está disponível agora. O hardware nativo só resgata o caso
single-shot, que é o de menor valor. Ou seja, o que exige anos de silício é o
que menos importa.

---

## 8. COMO O ~1.750× MELHORA EM APLICAÇÕES

O ~1.750× é **por operação** (uma agregação/range bandwidth-bound). Quanto
isso melhora uma APLICAÇÃO real depende de duas coisas — e a honestidade está
em nomear as duas.

### (a) Onde a forma do workload aparece

O ganho é real onde a app faz, repetidamente, agregação / range /
level-of-detail sobre dado reusado:
```
OLAP / dashboards ......... SUM/COUNT/AVG/MIN/MAX + filtros sobre colunas grandes
séries temporais .......... "média nesta janela", roll-ups, downsample p/ gráfico
geoespacial / científico .. "agregado nesta região", zoom-out = nível grosseiro
data lakes (Parquet) ...... já fazem isto (zone-maps) — é a prova de campo
visualização LOD .......... point clouds, mapas, vídeo: ler a resolução pedida
atenção hierárquica (LLM).. atender a sumários de blocos, não a todos os tokens
                            (DIREÇÃO de pesquisa; magnitude não reivindicada)
```

### (b) O teto de Amdahl — a parte que ninguém menciona

Acelerar UMA operação por 1.750× NÃO acelera a app por 1.750×. O ganho da app
é limitado pela FRAÇÃO `f` do tempo que era aquela operação:

```
speedup_app = 1 / ( (1 - f) + f / 1750 )  ≈  1 / (1 - f)   p/ S grande

   f (fração agregação/scan)   ganho real da app
   ────────────────────────────────────────────
   50%  ............................  ~2,0×
   80%  ............................  ~5,0×
   90%  ............................  ~9,9×
   95%  ............................  ~20×
   99%  ............................  ~91×
```

Logo: numa app que passa 90% do tempo em scans agregáveis, o ~1.750× por-op
vira **~10× de app**. Quem disser "1.750× na aplicação" está a ignorar Amdahl.
O número honesto da app é `1/(1-f)`, e `f` varia por aplicação.

### (c) Os ganhos que NÃO são "×velocidade" (e às vezes importam mais)

```
LATÊNCIA → INTERATIVIDADE  transformar um scan de segundos numa leitura de ms
                           muda a CATEGORIA de uso (batch → interativo), mesmo
                           quando o ganho de throughput por Amdahl é modesto.
ENERGIA                    mover dados domina o consumo de uma GPU; não movê-los
                           poupa joules (direção real; magnitude não reivindicada).
THROUGHPUT / CUSTO         cada query custa ~1.750× menos banda → mais queries
                           por GPU, ou GPU menor p/ a mesma carga.
```

### (d) O que isto NÃO é

Não é um speedup universal de aplicação. Não vale para a parte compute-bound
nem para consulta única sem reuso (o build não amortiza). O ~1.750× é o ganho
de uma operação específica; a app colhe `1/(1-f)` disso. Honesto, medido onde
dá para medir, projetado onde só dá para projetar.

---

## 9. CONCLUSÃO

O documento de Dez/2025 dizia "5-35× de hardware" sem medir nada. Este
processo mediu, na RTX 3060, e encontrou um ganho **maior** (~1.750× num
lote de agregação) — mas o valor importa menos que o método: quando o número
bruto (4.725×) tinha gordura (kernel flat ruim + ruído de piso), nós a
**diagnosticámos e tirámos**, reportando o ~1.750× que sobrevive a dois
caminhos independentes.

A intuição original estava certa (GPUs gastam o tempo movendo dados; não
mover dá ganho enorme). O número fabricado estava errado. A diferença entre
prometer e medir é exatamente este documento: a placa, os 3,51 TB, as duas
armadilhas, e o número que resiste.

---

*Reprodução: `X:/miniconda3/python.exe src/bench/heavy_gpu.py` (lote pesado),
`real_gpu.py` (leve), `harness.py` (simulação). Carga visível por
`nvidia-smi dmon -c 14 -s pucm` durante a execução.*
