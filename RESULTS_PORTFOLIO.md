# BH — BENCHMARK DE PORTFÓLIO (a tese-mãe)

Um ativo 4K serve o mix {thumb, 480p, 1080p, 4K, ROI}. Compara o BH (uma estrutura, múltiplas leituras) contra duas estratégias de especialista. Métrica: armazenamento (MB) e trabalho por operação (MB lidos).

- **Escada**: guarda N renditions WebP — storage alto, trabalho baixo.
- **Único**: guarda só o 4K WebP — storage mínimo, trabalho alto (decoda tudo a cada op).
- **BH**: uma estrutura — storage de 1 arquivo, trabalho de leitura parcial. A alegação: o melhor dos dois, QUANDO o arquivo é competitivo.


## gradient (sintético)

BH full PSNR = 55.5 dB (qualidade ~comparável ao WebP q85)

### Armazenamento total (servir o mix)

| estratégia | storage | vs BH |
|---|---|---|
| Escada (N WebP) | 0.066 MB | 25.86× |
| Único (1 WebP 4K) | 0.045 MB | 17.69× |
| BH (1 estrutura) | 0.003 MB | — |

### Trabalho por operação (MB lidos)

| operação | Escada | Único | BH |
|---|---|---|---|
| thumb | 0.001 | 0.045 | 0.003 |
| 480p | 0.004 | 0.045 | 0.003 |
| 1080p | 0.016 | 0.045 | 0.003 |
| 4K | 0.045 | 0.045 | 0.003 |
| ROI 512² | 0.045 | 0.045 | 0.000 |

## ui (screenshot)

BH full PSNR = inf dB (qualidade ~comparável ao WebP q85)

### Armazenamento total (servir o mix)

| estratégia | storage | vs BH |
|---|---|---|
| Escada (N WebP) | 0.073 MB | 0.04× |
| Único (1 WebP 4K) | 0.045 MB | 0.02× |
| BH (1 estrutura) | 1.932 MB | — |

### Trabalho por operação (MB lidos)

| operação | Escada | Único | BH |
|---|---|---|---|
| thumb | 0.003 | 0.045 | 0.101 |
| 480p | 0.009 | 0.045 | 0.624 |
| 1080p | 0.017 | 0.045 | 1.932 |
| 4K | 0.045 | 0.045 | 1.932 |
| ROI 512² | 0.045 | 0.045 | 0.124 |

## natural_city

BH full PSNR = 41.3 dB (qualidade ~comparável ao WebP q85)

### Armazenamento total (servir o mix)

| estratégia | storage | vs BH |
|---|---|---|
| Escada (N WebP) | 1.029 MB | 0.17× |
| Único (1 WebP 4K) | 0.664 MB | 0.11× |
| BH (1 estrutura) | 6.018 MB | — |

### Trabalho por operação (MB lidos)

| operação | Escada | Único | BH |
|---|---|---|---|
| thumb | 0.008 | 0.664 | 0.349 |
| 480p | 0.073 | 0.664 | 3.953 |
| 1080p | 0.284 | 0.664 | 6.018 |
| 4K | 0.664 | 0.664 | 6.018 |
| ROI 512² | 0.664 | 0.664 | 0.814 |

## LEITURA (corrigida pelos dados — não pela expectativa)

- **A opcionalidade sozinha NÃO basta para ganhar o portfólio.** O valor de
  "uma estrutura, muitas leituras" é real, mas a vitória medida exige uma
  segunda condição: o arquivo BH precisa ser COMPETITIVO EM TAMANHO. Só o
  `gradient` cumpriu — BH 0,003 MB serve todas as resoluções + ROI, 25,9×
  menor que a escada e 17,7× menor que o WebP único. Aí o BH é o melhor dos
  dois: storage de único + trabalho de escada.
- **Em `ui` e `natural`, o BH PERDE o portfólio.** O entropy coding do WebP
  comprime cada artefacto tão bem que guardar 4 renditions (escada) ainda
  pesa menos que um arquivo BH inchado (UI: BH 26× a escada; natural: 6×).
  O ganho do BH encolhe para operações de leitura parcial isoladas (só o
  thumbnail do natural; na ROI do natural ele até lê MAIS).
- **A lição que isto fecha:** opcionalidade é NECESSÁRIA mas não SUFICIENTE.
  O ganho de portfólio = (operações partilham a MESMA hierarquia) × (o ativo
  único é compressivamente competitivo). A primeira condição quase sempre
  vale (resolução e ROI partilham a decomposição espacial); a segunda é o
  gargalo — e é a mesma fronteira de sempre (compressão de coeficiente, fora
  do que o paradigma reivindica). Onde as duas valem, o BH é imbatível no
  mix; onde a segunda falha, o especialista ganha mesmo carregando N peças.
- **Nota de justiça:** o BH de `ui` saiu lossless (PSNR ∞) contra WebP q85
  (com perda) — comparação desfavorável ao BH nesse caso; ainda assim o
  veredicto de portfólio não muda de classe.
