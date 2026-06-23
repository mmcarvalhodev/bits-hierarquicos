# BH — PROJEÇÃO PARA HARDWARE NATIVO

Projeção a partir dos testes reais na RTX 3060. **Não é medição de hardware nativo** (que não existe). Proveniência por linha: [MEDIDO] = nossos testes · [PROJETADO] = físico/publicado · [ESPECULATIVO] = silício BH-nativo.

Parâmetros: BW=342 GB/s [MEDIDO] · piso lançamento=2,8 µs [MEDIDO] · latência memória=0,3 µs [PROJETADO] · energia=5 pJ/B [PROJETADO] · build near-memory [ESPECULATIVO].

## Projeções

| cenário | flat | BH software | ganho SW | BH nativo | ganho NATIVO |
|---|---|---|---|---|---|
| latência consulta única (1 GB) | 2.92 ms | 2.80 µs | 1,044× | 0.30 µs | **9,747×** |
| lote 6.000 consultas (3,51 TB) | 10.26 s | 5.85 ms | 1,754× | 1.80 ms | **5,702×** |
| energia (lote) | 17.6 J | — | — | 10.0 mJ | **1,755× menos** |

## Leitura honesta

- **Latência nativa recupera ~9×** sobre o software: o piso troca de lançamento de kernel (2,8 µs, artefacto de software) para latência de memória (0,3 µs, física). [PROJETADO]
- **Lote nativo (~5.700×)** assume build folded near-memory [ESPECULATIVO]; sem isso, fica no ~1.755× do software.
- **Energia (~1.755× menos) é a parte robusta**: a razão depende só do quociente de bytes movidos [MEDIDO]; o valor absoluto em Joules é que depende do pJ/B [PROJETADO].
- **Amdahl** governa a app: ganho de operação S vira 1/((1-f)+f/S) na aplicação. Nada aqui é speedup de app.
- **NUNCA reportar como medição.** Toda linha é projeção até existir silício. Spec: `BH_NATIVE_HARDWARE_MODEL_SPEC.md`.
