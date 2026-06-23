# BH CODEC MVP — RESULTADOS (F4)

Gerado pelo harness (`src/bench/harness.py`). Critérios de veredicto
declarados no topo do harness ANTES da medição — spec §1 e §7.

## VEREDICTO POR ALEGAÇÃO

- **C1 (decode progressivo): REFUTADA** — caso denso ≤1.2× geométrico: sim; preview sempre mais barato que rendition raw: não
- **C2 (ROI proporcional): CONFIRMADA** — payload ≤1.2× área em todas as imagens e regiões
- **C3 (compressão aceitável): REFUTADA** — sintetico: FALHOU, screenshot: FALHOU, natural: FALHOU (limites: sintético/screenshot ≤ PNG; natural ≤ 2× PNG; ruído excluído por ser adversarial declarado, spec §10 R1)

## TAMANHOS LOSSLESS (MB)

| classe | imagem | raw | PNG | BH s/ pirâmide | BH c/ pirâmide | BH/PNG | overhead pirâmide |
|---|---|---|---|---|---|---|---|
| sintetico | flat | 24.883 | 0.029 | 0.002 | 0.002 | 0.06× | 44.2% |
| sintetico | gradient | 24.883 | 0.168 | 10.312 | 13.406 | 61.25× | 30.0% |
| sintetico | shapes | 24.883 | 0.031 | 0.262 | 0.340 | 8.52× | 30.1% |
| sintetico | noise | 24.883 | 24.921 | 27.648 | 35.943 | 1.11× | 30.0% |
| screenshot | ui | 24.883 | 0.032 | 1.730 | 2.250 | 53.66× | 30.0% |
| natural | natural_city | 24.883 | 6.469 | 23.820 | 30.966 | 3.68× | 30.0% |
| natural | natural_forest | 24.883 | 3.346 | 20.199 | 26.259 | 6.04× | 30.0% |
| natural | natural_portrait | 24.883 | 1.705 | 14.332 | 18.632 | 8.41× | 30.0% |

## C1 — CURVA PROGRESSIVA (bytes lidos por resolução)

| imagem | alvo | bytes (MB) | fração arquivo | fração geométrica | rendition raw (MB) |
|---|---|---|---|---|---|
| flat | thumb | 0.002 | 100.00% | 0.52% | 0.097 |
| flat | 480p | 0.002 | 100.00% | 2.08% | 0.389 |
| flat | 1080p | 0.002 | 100.00% | 33.33% | 6.221 |
| gradient | thumb | 0.141 | 1.05% | 0.52% | 0.097 |
| gradient | 480p | 0.562 | 4.19% | 2.08% | 0.389 |
| gradient | 1080p | 6.493 | 48.44% | 33.33% | 6.221 |
| shapes | thumb | 0.028 | 8.32% | 0.52% | 0.097 |
| shapes | 480p | 0.057 | 16.84% | 2.08% | 0.389 |
| shapes | 1080p | 0.210 | 61.82% | 33.33% | 6.221 |
| noise | thumb | 0.141 | 0.39% | 0.52% | 0.097 |
| noise | 480p | 0.562 | 1.56% | 2.08% | 0.389 |
| noise | 1080p | 8.986 | 25.00% | 33.33% | 6.221 |
| ui | thumb | 0.101 | 4.48% | 0.52% | 0.097 |
| ui | 480p | 0.289 | 12.85% | 2.08% | 0.389 |
| ui | 1080p | 1.216 | 54.06% | 33.33% | 6.221 |
| natural_city | thumb | 0.141 | 0.45% | 0.52% | 0.097 |
| natural_city | 480p | 0.555 | 1.79% | 2.08% | 0.389 |
| natural_city | 1080p | 8.312 | 26.84% | 33.33% | 6.221 |
| natural_forest | thumb | 0.141 | 0.54% | 0.52% | 0.097 |
| natural_forest | 480p | 0.553 | 2.11% | 2.08% | 0.389 |
| natural_forest | 1080p | 7.990 | 30.43% | 33.33% | 6.221 |
| natural_portrait | thumb | 0.130 | 0.70% | 0.52% | 0.097 |
| natural_portrait | 480p | 0.481 | 2.58% | 2.08% | 0.389 |
| natural_portrait | 1080p | 5.910 | 31.72% | 33.33% | 6.221 |

## C2 — ROI (custo por área)

| imagem | área | payload lido | total lido | seeks |
|---|---|---|---|---|
| flat | 1.00% | 0.44% | 15.72% | 3 |
| flat | 6.25% | 0.44% | 15.72% | 3 |
| flat | 25.00% | 0.44% | 15.72% | 3 |
| gradient | 1.00% | 0.75% | 8.38% | 3,362 |
| gradient | 6.25% | 4.65% | 11.98% | 18,846 |
| gradient | 25.00% | 18.73% | 24.99% | 74,702 |
| shapes | 1.00% | 0.69% | 8.38% | 98 |
| shapes | 6.25% | 3.32% | 10.81% | 916 |
| shapes | 25.00% | 21.02% | 27.14% | 2,934 |
| noise | 1.00% | 0.75% | 8.39% | 216 |
| noise | 6.25% | 4.69% | 12.02% | 540 |
| noise | 25.00% | 18.75% | 25.00% | 1,080 |
| ui | 1.00% | 0.47% | 8.14% | 473 |
| ui | 6.25% | 4.22% | 11.60% | 1,415 |
| ui | 25.00% | 22.35% | 28.33% | 2,960 |
| natural_city | 1.00% | 0.82% | 8.45% | 931 |
| natural_city | 6.25% | 5.26% | 12.55% | 3,436 |
| natural_city | 25.00% | 20.90% | 26.99% | 16,193 |
| natural_forest | 1.00% | 0.62% | 8.27% | 3,267 |
| natural_forest | 6.25% | 4.02% | 11.40% | 20,030 |
| natural_forest | 25.00% | 17.91% | 24.22% | 66,856 |
| natural_portrait | 1.00% | 1.00% | 8.62% | 1,046 |
| natural_portrait | 6.25% | 5.64% | 12.90% | 6,985 |
| natural_portrait | 25.00% | 20.13% | 26.28% | 32,521 |

## C3 LOSSY — BH vs JPEG a PSNR equivalente

| imagem | threshold | BH (MB) | PSNR BH | JPEG q | JPEG (MB) | PSNR JPEG | BH/JPEG |
|---|---|---|---|---|---|---|---|
| flat | 8 | 0.002 | inf | 10 | 0.130 | 42.5 | 0.0× |
| flat | 24 | 0.002 | inf | 10 | 0.130 | 42.5 | 0.0× |
| flat | 64 | 0.002 | inf | 10 | 0.130 | 42.5 | 0.0× |
| gradient | 8 | 0.008 | 43.8 | 35 | 0.135 | 44.4 | 0.1× |
| gradient | 24 | 0.003 | 38.1 | 15 | 0.132 | 37.5 | 0.0× |
| gradient | 64 | 0.002 | 26.3 | 10 | 0.132 | 34.0 | 0.0× |
| shapes | 8 | 0.262 | inf | 10 | 0.151 | 31.2 | 1.7× |
| shapes | 24 | 0.261 | 73.0 | 95 | 0.255 | 41.1 | 1.0× |
| shapes | 64 | 0.260 | 47.4 | 95 | 0.255 | 41.1 | 1.0× |
| noise | 8 | 27.648 | inf | 10 | 0.915 | 10.9 | 30.2× |
| noise | 24 | 27.648 | inf | 10 | 0.915 | 10.9 | 30.2× |
| noise | 64 | 27.646 | 61.5 | 95 | 9.729 | 12.7 | 2.8× |
| ui | 8 | 1.730 | inf | 10 | 0.222 | 32.4 | 7.8× |
| ui | 24 | 1.710 | 48.4 | 90 | 0.580 | 47.8 | 2.9× |
| ui | 64 | 0.783 | 29.5 | 10 | 0.222 | 32.4 | 3.5× |
| natural_city | 8 | 7.927 | 44.4 | 65 | 0.741 | 44.5 | 10.7× |
| natural_city | 24 | 2.441 | 36.1 | 25 | 0.386 | 35.6 | 6.3× |
| natural_city | 64 | 0.461 | 29.5 | 10 | 0.219 | 30.6 | 2.1× |
| natural_forest | 8 | 2.247 | 44.4 | 55 | 0.358 | 44.4 | 6.3× |
| natural_forest | 24 | 0.573 | 36.6 | 15 | 0.175 | 36.3 | 3.3× |
| natural_forest | 64 | 0.121 | 29.3 | 10 | 0.161 | 33.9 | 0.8× |
| natural_portrait | 8 | 1.312 | 44.7 | 45 | 0.235 | 44.5 | 5.6× |
| natural_portrait | 24 | 0.352 | 36.9 | 10 | 0.149 | 36.9 | 2.4× |
| natural_portrait | 64 | 0.097 | 29.0 | 10 | 0.149 | 36.9 | 0.7× |

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
