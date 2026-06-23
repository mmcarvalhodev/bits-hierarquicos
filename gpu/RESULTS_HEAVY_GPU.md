# BH GPU — TESTE PESADO (RTX 3060)

GPU: NVIDIA GeForce RTX 3060. Array 2.0 GB. 6,000 consultas de agregação de range (kernel CUDA real no flat). Tráfego flat 3.51 TB.

Verificação flat vs BH: OK (erro rel máx 4.0e-10).

| lado | tempo | nota |
|---|---|---|
| FLAT (meu kernel varre 3.51 TB) | 26.28 s | 134 GB/s = 37% do teto |
| FLAT ideal (bandwidth puro, 360 GB/s) | 9.76 s | estimativa do limite |
| BH (lê agregado) | 5.6 ms | + build único 86 ms |

**Speedup honesto: 1,756× (vs flat IDEAL) a 4,725× (vs meu kernel).**

## LEITURA HONESTA

- **A carga foi real:** o flat varreu 3.51 TB de VRAM e empurrou a placa por 26 s (SM a 100%). MAS sustentou só 134 GB/s = 37% do teto — meu kernel (1 bloco/consulta, redução ingênua) é SUBÓTIMO, limitado por ocupação, não por banda pura.
- **Por isso o speedup honesto é um INTERVALO:** 4,725× contra o meu kernel, mas só ~1,756× contra um flat perfeito (bandwidth-bound a 360 GB/s). O número justo é o menor — parte do 213× era o meu flat ser ruim, não o BH ser mágico.
- **Mesmo no limite honesto, o BH ganha ~1,756×:** responde as 6,000 consultas em 6 ms lendo o agregado, em vez de mover 3.51 TB. Mesma resposta, verificada. O ganho é NÃO mover os dados — isso nenhum kernel flat melhora, porque os dados existem.
- **Custo único:** build do agregado 86 ms, desprezível perto do lote. Vale p/ agregação/range sobre dado reusado; não p/ consulta única nem kernel compute-bound.
