# BH FILME (proxy 30s) — RESULTADOS

720 frames (30s @ 24fps) · 256×256 · 3 camadas co-registradas (RGB+depth+seg). Proxy: ratios transferem para 4K; a fração estrutura/payload não depende da resolução.

## TOTAIS (unidades de bytes do modelo)

| estratégia | total | vs independente |
|---|---|---|
| 1. independente | 4.217 M | 1.00× |
| 2. temporal | 2.549 M | 1.65× |
| 3. wafer (still) | 3.749 M | 1.12× |
| 4. wafer + temporal | 1.981 M | 2.13× |

## A HIPÓTESE DO MÁRCIO, MEDIDA

- **Redundância temporal esvazia o payload:** temporal é 1.7× menor que independente — a maior parte do filme é estática e colapsa em skip-leaves.
- **A fração-estrutura SOBE com o temporal:** independente = 16.7% estrutura; temporal = 33.4% estrutura. O payload encolheu, a estrutura virou fração grande.
- **O wafer ganha mais SOBRE o temporal:** ganho do wafer em still = 1.12×; sobre o temporal = 1.29×. Quando a estrutura domina (temporal), partilhá-la entre camadas passa a valer.
- **Melhor combinação (wafer+temporal): 2.1× menor que independente.**

## LEITURA HONESTA

- A predição temporal (skip de regiões estáticas) é o que codecs de vídeo já fazem — não é novo. O que o teste mostra é o EFEITO COMPOSTO: ao esvaziar o payload, o temporal faz a estrutura virar o custo dominante, e SÓ ENTÃO partilhar estrutura entre camadas co-registradas (o wafer) move a agulha — o que não acontecia na imagem parada.
- Confirma a intuição do filme: o paradigma precisa de ESCALA + REDUNDÂNCIA, não de tamanho. Um filme tem as duas; uma foto, nenhuma.
- Proxy a 256×256: os ratios são o resultado; o 4K muda o tamanho absoluto, não as frações (estrutura/payload é invariante de escala).
