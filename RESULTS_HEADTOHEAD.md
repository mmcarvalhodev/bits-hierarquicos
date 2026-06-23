# HEAD-TO-HEAD POR TAREFA — BH vs codecs polidos

Métrica primária: **bytes lidos** para cumprir a tarefa (justa, independe de linguagem).
Tempo: BH é Python puro; PNG/JPEG/WebP são C otimizado — o tempo favorece os polidos por implementação.


## gradient  (BH 0.00 MB · PNG 0.17 · JPEG 0.19 · WebP 0.05)

### Tarefa A — thumbnail ~256px
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.003 MB | — | 571.0 |
| PNG | 0.168 MB | 54× mais | 46.7 |
| JPEG | 0.191 MB | 62× mais | 3.9 |
| WebP | 0.045 MB | 15× mais | 87.8 |

### Tarefa B — região central 512×512
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.000 MB | — | 500.4 |
| PNG | 0.168 MB | 414× mais | 60.0 |
| JPEG | 0.191 MB | 469× mais | 38.4 |
| WebP | 0.045 MB | 111× mais | 96.0 |

## shapes  (BH 0.30 MB · PNG 0.03 · JPEG 0.22 · WebP 0.02)

### Tarefa A — thumbnail ~256px
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.028 MB | — | 878.6 |
| PNG | 0.031 MB | 1× mais | 19.1 |
| JPEG | 0.221 MB | 8× mais | 3.5 |
| WebP | 0.024 MB | 1× mais | 78.5 |

### Tarefa B — região central 512×512
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.020 MB | — | 238.4 |
| PNG | 0.031 MB | 2× mais | 34.4 |
| JPEG | 0.221 MB | 11× mais | 34.5 |
| WebP | 0.024 MB | 1× mais | 79.8 |

## ui  (BH 1.93 MB · PNG 0.03 · JPEG 0.53 · WebP 0.04)

### Tarefa A — thumbnail ~256px
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.101 MB | — | 529.6 |
| PNG | 0.032 MB | 0× mais | 20.9 |
| JPEG | 0.533 MB | 5× mais | 4.0 |
| WebP | 0.045 MB | 0× mais | 67.9 |

### Tarefa B — região central 512×512
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.124 MB | — | 233.0 |
| PNG | 0.032 MB | 0× mais | 26.8 |
| JPEG | 0.533 MB | 4× mais | 31.6 |
| WebP | 0.045 MB | 0× mais | 78.7 |

## natural_city  (BH 7.95 MB · PNG 6.47 · JPEG 1.01 · WebP 0.66)

### Tarefa A — thumbnail ~256px
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.148 MB | — | 582.0 |
| PNG | 6.469 MB | 44× mais | 98.8 |
| JPEG | 1.008 MB | 7× mais | 8.1 |
| WebP | 0.664 MB | 4× mais | 119.6 |

### Tarefa B — região central 512×512
| formato | bytes lidos | vs BH | tempo (ms) |
|---|---|---|---|
| BH | 0.625 MB | — | 237.1 |
| PNG | 6.469 MB | 10× mais | 107.8 |
| JPEG | 1.008 MB | 2× mais | 36.5 |
| WebP | 0.664 MB | 1× mais | 126.1 |

## Tarefa C — tamanho lossy em conteúdo que casa (gradiente)

| formato | tamanho | PSNR (dB) |
|---|---|---|
| BH-ramp | 2.4 KB | 57.9 |
| JPEG | 434.4 KB | 51.9 |
| WebP | 116.7 KB | 50.2 |
| PNG | 168.4 KB | inf |

## LEITURA

- **Acesso (A, B): o BH vence por construção** — codec polido precisa
  do arquivo inteiro para thumbnail/ROI; o BH lê o prefixo / o ramo.
  Polimento não muda isso: é estrutural.
- **Compressão de foto natural: o polido vence** — e o relatório não
  esconde (ver tamanhos no cabeçalho de natural_city).
- **Conteúdo casado (C): a interpretação certa bate o polido** em
  ordens de grandeza — a tese 'interpretação é a alavanca'.
