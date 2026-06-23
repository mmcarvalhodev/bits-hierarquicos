# BH GPU — TESTE REAL (RTX 3060)

GPU: NVIDIA GeForce RTX 3060. 256,000,000 float32 = 1.0 GB em VRAM. Tempo por CUDA events, mediana de 200 chamadas (30 de warmup).

BH = ler o agregado pré-computado (prefix-sum dos blocos). flat = redução lendo a VRAM. Emulação em software; sem hardware BH-nativo.

| tarefa | bytes flat | tempo flat | tempo BH | speedup REAL | razão de bytes | banda efetiva flat |
|---|---|---|---|---|---|---|
| Redução total (1 GB) | 1024 MB | 2991.1 µs | 2.8 µs | **1,087×** | 128,000,000× | 342 GB/s |
| Agregação range 25% (256 MB) | 256 MB | 752.5 µs | 2.8 µs | **264×** | 16,000,000× | 340 GB/s |

## LEITURA HONESTA

- **O speedup real é GRANDE mas MENOR que a razão de bytes.** A razão de bytes da redução total é 128,000,000×, mas o tempo real deu 1,087× — a leitura BH (O(1)) bate no PISO de overhead de lançamento de kernel (~µs fixos). O hardware mostra o piso que a simulação não modelou — fator ~117,768× de diferença.
- **A banda efetiva do flat confirma bandwidth-bound:** a redução de 1 GB roda perto do teto de ~360 GB/s da 3060 — ou seja, o flat está mesmo limitado por memória, exatamente a premissa da ponte bytes→tempo. Logo o ganho do BH é real, não artefato.
- **O que isto é:** BH como layout de software em GPU existente (Fase 1 do doc). O ganho vem de NÃO mover os dados — o agregado já está pronto. Para cargas dominadas por agregação/LOD/range, é real e mensurável aqui.
- **O que isto NÃO é:** não é o hardware BH-nativo do doc; e a vantagem encolhe quando o trabalho BH é grande o suficiente para sair do piso de overhead. Em range pequeno, flat e BH convergem. Sem milagre — física.
- **Custo único de build (amortização):** construir o prefix/agregado custou 15311 µs uma vez. Vale a pena a partir de ~5 consultas que reusem o agregado; para UMA consulta só, o flat (sem build) ganha. O BH é p/ dado consultado muitas vezes — exatamente a premissa de 'conversa é dado' / ativo reusado.
