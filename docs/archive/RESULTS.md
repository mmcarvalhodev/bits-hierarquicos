# BH CODEC MVP — RESULTADOS (F4)

Gerado pelo harness (`src/bench/harness.py`). Critérios de veredicto
declarados no topo do harness ANTES da medição — spec §1 e §7.

## VEREDICTO POR ALEGAÇÃO

- **C1 (decode progressivo): REFUTADA** — caso denso ≤1.2× geométrico: não; preview sempre mais barato que rendition raw: não
- **C2 (ROI proporcional): REFUTADA** — payload ≤1.2× área em todas as imagens e regiões
- **C3 (compressão aceitável): REFUTADA** — sintetico: FALHOU, screenshot: FALHOU, natural: FALHOU (limites: sintético/screenshot ≤ PNG; natural ≤ 2× PNG; ruído excluído por ser adversarial declarado, spec §10 R1)

## TAMANHOS LOSSLESS (MB)

| classe | imagem | raw | PNG | BH s/ pirâmide | BH c/ pirâmide | BH/PNG | overhead pirâmide |
|---|---|---|---|---|---|---|---|
| sintetico | flat | 24.883 | 0.029 | 0.002 | 0.002 | 0.06× | 44.2% |
| sintetico | gradient | 24.883 | 0.168 | 9.666 | 10.966 | 57.41× | 13.5% |
| sintetico | shapes | 24.883 | 0.031 | 0.252 | 0.300 | 8.19× | 19.4% |
| sintetico | noise | 24.883 | 24.921 | 25.575 | 27.649 | 1.03× | 8.1% |
| screenshot | ui | 24.883 | 0.032 | 1.651 | 1.932 | 51.20× | 17.0% |
| natural | natural_city | 24.883 | 6.469 | 21.728 | 23.609 | 3.36× | 8.7% |
| natural | natural_forest | 24.883 | 3.346 | 17.904 | 19.655 | 5.35× | 9.8% |
| natural | natural_portrait | 24.883 | 1.705 | 12.380 | 13.642 | 7.26× | 10.2% |

## C1 — CURVA PROGRESSIVA (bytes lidos por resolução)

| imagem | alvo | bytes (MB) | fração arquivo | fração geométrica | rendition raw (MB) |
|---|---|---|---|---|---|
| flat | thumb | 0.002 | 100.00% | 0.52% | 0.097 |
| flat | 480p | 0.002 | 100.00% | 2.08% | 0.389 |
| flat | 1080p | 0.002 | 100.00% | 33.33% | 6.221 |
| gradient | thumb | 0.141 | 1.29% | 0.52% | 0.097 |
| gradient | 480p | 0.582 | 5.31% | 2.08% | 0.389 |
| gradient | 1080p | 10.966 | 100.00% | 33.33% | 6.221 |
| shapes | thumb | 0.028 | 9.43% | 0.52% | 0.097 |
| shapes | 480p | 0.057 | 19.08% | 2.08% | 0.389 |
| shapes | 1080p | 0.300 | 100.00% | 33.33% | 6.221 |
| noise | thumb | 0.141 | 0.51% | 0.52% | 0.097 |
| noise | 480p | 0.562 | 2.03% | 2.08% | 0.389 |
| noise | 1080p | 27.649 | 100.00% | 33.33% | 6.221 |
| ui | thumb | 0.101 | 5.22% | 0.52% | 0.097 |
| ui | 480p | 0.289 | 14.96% | 2.08% | 0.389 |
| ui | 1080p | 1.932 | 100.00% | 33.33% | 6.221 |
| natural_city | thumb | 0.141 | 0.60% | 0.52% | 0.097 |
| natural_city | 480p | 0.557 | 2.36% | 2.08% | 0.389 |
| natural_city | 1080p | 23.609 | 100.00% | 33.33% | 6.221 |
| natural_forest | thumb | 0.141 | 0.72% | 0.52% | 0.097 |
| natural_forest | 480p | 0.555 | 2.83% | 2.08% | 0.389 |
| natural_forest | 1080p | 19.655 | 100.00% | 33.33% | 6.221 |
| natural_portrait | thumb | 0.131 | 0.96% | 0.52% | 0.097 |
| natural_portrait | 480p | 0.481 | 3.52% | 2.08% | 0.389 |
| natural_portrait | 1080p | 13.642 | 100.00% | 33.33% | 6.221 |

## C2 — ROI (custo por área)

| imagem | área | payload lido | total lido | seeks |
|---|---|---|---|---|
| flat | 1.00% | 0.44% | 15.72% | 3 |
| flat | 6.25% | 0.44% | 15.72% | 3 |
| flat | 25.00% | 0.44% | 15.72% | 3 |
| gradient | 1.00% | 0.87% | 4.79% | 996 |
| gradient | 6.25% | 5.43% | 9.17% | 5,572 |
| gradient | 25.00% | 21.90% | 24.98% | 21,660 |
| shapes | 1.00% | 0.76% | 6.17% | 59 |
| shapes | 6.25% | 3.68% | 8.93% | 634 |
| shapes | 25.00% | 23.24% | 27.43% | 1,823 |
| noise | 1.00% | 0.92% | 3.40% | 108 |
| noise | 6.25% | 5.77% | 8.13% | 270 |
| noise | 25.00% | 23.08% | 25.00% | 540 |
| ui | 1.00% | 0.54% | 5.36% | 205 |
| ui | 6.25% | 4.77% | 9.39% | 752 |
| ui | 25.00% | 25.25% | 28.88% | 1,571 |
| natural_city | 1.00% | 1.01% | 3.64% | 188 |
| natural_city | 6.25% | 6.51% | 8.99% | 559 |
| natural_city | 25.00% | 25.82% | 27.79% | 1,919 |
| natural_forest | 1.00% | 0.71% | 3.66% | 660 |
| natural_forest | 6.25% | 4.61% | 7.44% | 3,659 |
| natural_forest | 25.00% | 21.34% | 23.68% | 10,487 |
| natural_portrait | 1.00% | 1.25% | 4.30% | 327 |
| natural_portrait | 6.25% | 7.05% | 9.92% | 1,700 |
| natural_portrait | 25.00% | 24.83% | 27.15% | 6,977 |

## C3 LOSSY — BH vs JPEG a PSNR equivalente

| imagem | threshold | BH (MB) | PSNR BH | JPEG q | JPEG (MB) | PSNR JPEG | BH/JPEG |
|---|---|---|---|---|---|---|---|
| flat | 8 | 0.002 | inf | 10 | 0.130 | 42.5 | 0.0× |
| flat | 24 | 0.002 | inf | 10 | 0.130 | 42.5 | 0.0× |
| flat | 64 | 0.002 | inf | 10 | 0.130 | 42.5 | 0.0× |
| gradient | 8 | 0.002 | 55.5 | 95 | 0.434 | 51.9 | 0.0× |
| gradient | 24 | 0.002 | 55.5 | 95 | 0.434 | 51.9 | 0.0× |
| gradient | 64 | 0.002 | 34.3 | 10 | 0.132 | 34.0 | 0.0× |
| shapes | 8 | 0.251 | 81.1 | 95 | 0.255 | 41.1 | 1.0× |
| shapes | 24 | 0.251 | 55.9 | 95 | 0.255 | 41.1 | 1.0× |
| shapes | 64 | 0.207 | 34.9 | 20 | 0.163 | 34.4 | 1.3× |
| noise | 8 | 25.575 | inf | 10 | 0.915 | 10.9 | 28.0× |
| noise | 24 | 25.575 | inf | 10 | 0.915 | 10.9 | 28.0× |
| noise | 64 | 25.572 | 61.5 | 95 | 9.729 | 12.7 | 2.6× |
| ui | 8 | 1.651 | inf | 10 | 0.222 | 32.4 | 7.4× |
| ui | 24 | 1.606 | 41.7 | 55 | 0.417 | 41.7 | 3.9× |
| ui | 64 | 0.742 | 26.2 | 10 | 0.222 | 32.4 | 3.3× |
| natural_city | 8 | 5.747 | 41.7 | 60 | 0.716 | 42.2 | 8.0× |
| natural_city | 24 | 1.604 | 32.9 | 15 | 0.262 | 33.1 | 6.1× |
| natural_city | 64 | 0.252 | 25.9 | 10 | 0.219 | 30.6 | 1.1× |
| natural_forest | 8 | 1.031 | 41.4 | 35 | 0.235 | 42.0 | 4.4× |
| natural_forest | 24 | 0.245 | 32.6 | 10 | 0.161 | 33.9 | 1.5× |
| natural_forest | 64 | 0.050 | 25.0 | 10 | 0.161 | 33.9 | 0.3× |
| natural_portrait | 8 | 0.870 | 41.3 | 25 | 0.189 | 41.5 | 4.6× |
| natural_portrait | 24 | 0.241 | 33.0 | 10 | 0.149 | 36.9 | 1.6× |
| natural_portrait | 64 | 0.065 | 23.9 | 10 | 0.149 | 36.9 | 0.4× |

## NOTAS DE HONESTIDADE

- Fotos naturais vêm de JPEG decodificado (Lorem Picsum/Unsplash): o ruído
  de bloco do JPEG degrada a quadtree lossless — o cenário real seria RAW
  de sensor, provavelmente pior ainda (mais ruído). O número fica como está.
- `noise` está nas tabelas mas fora do veredicto C3: é o adversarial
  declarado (spec §10 R1) — custo acima do raw é o esperado e foi medido.
- ROI paga piso fixo de estrutura (~8% do arquivo) — candidato a índice de
  ranks na v1; ver coluna 'total lido' vs 'payload lido'.
- PSNR do lossy BH em threshold alto vem com artefactos de bloco visíveis
  (spec §10 R3): PSNR não captura qualidade perceptual.
