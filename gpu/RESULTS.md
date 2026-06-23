# BH GPU SIM — RESULTADOS

Array de 16,000,000 float32 (64 MB). Métrica: **bytes movidos da DRAM**. Linha de cache 128 B; nó 16 B; banda 3.35 TB/s (HBM3 classe H100).

**NÃO é benchmark de GPU.** É simulação de movimento de dados. A coluna tempo assume kernel **bandwidth-bound** (tempo ≈ bytes/banda) — hipótese, não medição. O BH é PENALIZADO por scatter (cada nó = 1 linha inteira).

## CARGA — bytes movidos (flat vs BH)

| query | flat | BH | menos dados | tempo flat→BH |
|---|---|---|---|---|
| Q1 agregação range 25% (×1000) | 16.00 GB | 2.44 MB | **6,564×** | 4776.1→0.73 µs |
| Q2 level-of-detail (1 passada) | 64.00 MB | 4.1 KB | **15,625×** | 19.1→0.00 µs |
| Q3 acoplado a contexto (1M itens) | 256.00 MB | 4.00 MB | **64×** | 76.4→1.19 µs |
| Q4 filtro v>p99 (clusterizado) | 64.00 MB | 4.20 MB | **15×** | 19.1→1.25 µs |
| **TOTAL da carga** | **16.38 GB** | **10.64 MB** | **1,540×** | 4891→3.2 µs |

## VEREDICTO POR ALEGAÇÃO

- **G1 (agregação/LOD movem ordens de grandeza menos): CONFIRMADA** — agregação de range 6,564× menos dados; LOD 15,625× menos. O agregado vive nos nós; o flat tem de varrer.
- **G2 (acoplado a contexto ~ ordem do '50%' do doc): CONFIRMADA com folga** — 64× menos: contexto embutido vs lookup espalhado. O doc de Dez/2025 estimou 'metade dos acessos'; medido, é mais — mas a forma é a mesma (menos viagens à memória).
- **G3 (fronteira): DECLARADA** — em range pequeno (≤1 bloco) o BH não ganha (mede igual ao flat). A ponte para tempo só vale bandwidth-bound; kernel compute-bound não vê nada disto. E o build da árvore é custo único, amortizado sobre a carga.

## LEITURA HONESTA

- **O que isto fecha:** o doc de Dez/2025 prometeu 5-35× de hardware sem medir. Esta simulação mede a ÚNICA coisa honesta — movimento de dados — e mostra que, para carga dominada por agregação/LOD/contexto, o layout hierárquico move ordens de grandeza menos bytes. Isso é real e é a raiz da intuição original (GPUs gastam o tempo movendo dados).
- **O que isto NÃO prova:** não é ×speedup de GPU. Vira tempo só se o kernel for bandwidth-bound (a maioria dos kernels de dados/IA é, mas não todos). Scatter da árvore foi penalizado e ainda assim ganha — mas em hardware real o padrão de acesso importa, e o ganho pleno exigiria o memory controller ciente da hierarquia que o doc imaginou (não existe).
- **A ponte honesta:** menos bytes movidos → menos tempo SE bandwidth-bound. É uma hipótese nomeada, não um relógio. O número real de hardware só sai com kernel + GPU — fora do escopo desta simulação.
