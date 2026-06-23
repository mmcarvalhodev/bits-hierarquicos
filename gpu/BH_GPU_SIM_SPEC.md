# BH GPU SIM — SPEC
## Simulação honesta de movimento de dados em workload GPU intensivo

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Origem:** fecha o laço com o documento de Dez/2025 (GPUs gastam 80-90% dos
ciclos movendo dados) — substituindo os números de hardware FABRICADOS de lá
por uma medição honesta da única coisa que de facto era mensurável.

---

## 0. O QUE ISTO É E O QUE NÃO É

```
NÃO É um benchmark de GPU — sem kernel CUDA, sem hardware. Nada de "×speedup".
NÃO É o hardware BH do doc original (memory controller ciente da hierarquia
   não existe).
É uma SIMULAÇÃO de MOVIMENTO DE DADOS: bytes movidos da DRAM + linhas de
   cache tocadas, layout flat vs BH, sobre uma carga representativa.
```

**Por que movimento de dados é a métrica certa:** workloads de IA/dados em
GPU são memory-bandwidth-bound (o "memory wall"). Para um kernel
bandwidth-bound, tempo ≈ bytes_movidos / largura_de_banda. Essa é a ÚNICA
ponte honesta para tempo — declarada como hipótese, não como medição de
relógio.

**Honestidade de scatter:** GPU ama leitura contígua coalescida. A travessia
de árvore do BH é acesso espalhado (pequeno, scattered) — anti-coalescido.
A simulação PENALIZA o BH por isto (cada nó tocado = 1 linha de cache
inteira, mesmo usando 16 B dela). Se o BH ganha mesmo penalizado, é real.

## 1. MODELO DE MEMÓRIA

```
linha de cache .... 128 B (setor GPU típico; conservador)
elemento .......... float32 = 4 B  → 32 elementos/linha
nó de agregado .... 16 B (sum+min+max f32 + count u32)
largura de banda .. 3.35 TB/s (HBM3, classe H100) — só p/ estimar tempo
bloco-folha ....... 32 elementos = 1 linha de cache (granularidade natural)
```

## 2. CARGA (workload representativo de dados em GPU)

```
Q1 agregação de range  redução (sum) sobre faixa — analytics/científico
Q2 level-of-detail     passada grosseira/aproximada sobre todo o array
Q3 acoplado a contexto cada item precisa do valor + seu contexto/agregado
                       (o exemplo motivador do doc: token + contexto)
Q4 filtro com poda     redução condicional (count where v>t) em dado clusterizado
```

## 3. CUSTO POR QUERY (bytes movidos da DRAM)

```
FLAT (convencional, contíguo/coalescido):
  range agg  → lê todos os elementos da faixa = ceil(faixa/32) linhas × 128 B
  LOD        → lê o array inteiro (precisa reduzir tudo)
  contexto   → valor (1 linha) + contexto em outro lugar (1 linha scattered) = 2/item
  filtro     → lê tudo (checa cada elemento)

BH (hierárquico, contexto embutido) — COM penalidade de scatter:
  range agg  → nós cobertos (O(log) × 1 linha cada, conservador) + 2 blocos fronteira
  LOD        → só os níveis do topo (poucas linhas)
  contexto   → contexto embutido adjacente → ~1 linha/item
  filtro     → poda por min/max → só os ramos que sobrevivem
```

## 4. ALEGAÇÕES

```
G1 — agregação/LOD movem ORDENS DE GRANDEZA menos dados no BH (o agregado
     vive nos nós; flat tem de varrer). Confirmada se bytes_bh ≪ bytes_flat.
G2 — acoplado a contexto: ~2× menos (o "50% de redução de acessos" do doc,
     agora medido — não os 5-35× fabricados).
G3 — FRONTEIRA: scatter pode comer o ganho em acessos pequenos; carga
     compute-bound não vê benefício nenhum (a ponte tempo só vale
     bandwidth-bound); o build da árvore é custo único amortizado.
```

## 5. PROJETO

```
gpu/
├── BH_GPU_SIM_SPEC.md
├── src/bhgpu/sim.py     # pirâmide + custos de movimento + carga + tempo
├── tests/test_sim.py    # agregados exatos; contabilidade de linha sã
└── RESULTS.md
```

Stack: Python 3.13 + NumPy. Gate: agregados do BH batem o flat (exato) antes
de medir movimento.

---

*O doc de Dez/2025 prometeu 5-35× de hardware sem medir nada. Esta simulação
mede a única coisa honesta — bytes movidos — e diz exatamente quando isso
vira tempo e quando não vira.*
