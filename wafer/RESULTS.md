# BH WAFER MVP — RESULTADOS

Múltiplas camadas co-registradas sobre UMA hierarquia. Métrica: bytes de estrutura (partilhada no wafer) + payload (cobrado por Shannon). Comparado contra K árvores independentes.

Lado 512×512. Estrutura = 1 byte por nó interno.

## VEREDICTO POR ALEGAÇÃO

- **W1 (amortização de estrutura): CONFIRMADA (mas pequena)** — a estrutura É partilhada ~4.0× (gravada 1× em vez de 4×), MAS é só 4.0% do total → ganho total só 1.12×. Estrutura-sozinha é alavanca fraca quando o payload domina. O ganho grande exige correlação entre-camadas (não implementado).
- **W2 (teto de Shannon): CONFIRMADA** — payload do wafer == soma dos independentes (overhead 0 B). Só a estrutura é partilhada; conteúdo não é mágica.
- **W3 (fronteira, desalinhado): CONFIRMADA** — partições independentes: wafer 0.32× (PERDE), união super-subdivide.

- **W4 (correlação entre-camadas): EXPERIMENTAL** — no cenário C+, luminância derivada do RGB economiza 176.1 KB de payload; ganho total vai para 0.78×.

- **W5 (base + refinamentos): EXPERIMENTAL** — no cenário C++, a árvore RGB não é arrastada pela segmentação; ganho total vai para 1.12×.

## CENÁRIOS — estrutura + payload (KB)

| cenário | wafer estrut | wafer payload | wafer total | indep total | ganho |
|---|---|---|---|---|---|
| A — co-registrado (mesma partição) | 0.8 | 20.1 | 20.9 | 23.4 | 1.12× |
| B — desalinhado (partições independentes) | 2.0 | 72.4 | 74.4 | 23.6 | 0.32× (perde) |
| C — foto real + luminância + segmentação | 58.7 | 1232.5 | 1291.2 | 869.8 | 0.67× (perde) |
| C+ - foto + luminancia derivada do RGB + segmentacao | 58.7 | 1056.5 | 1115.2 | 869.8 | 0.78× (perde) |
| C++ - arvore RGB + lum derivada + refinamento da segmentacao | 58.7 | 714.6 | 773.3 | 869.8 | 1.12× |

## DETALHE — onde está o ganho (cenário A)

- Estrutura: wafer **0.8 KB** vs independente **3.3 KB** → 2.5 KB poupados (a estrutura replicada 4× que o wafer grava 1×).
- Payload: wafer 20.1 KB == independente 20.1 KB (Shannon: idêntico).
- **O ganho é exatamente a estrutura não-replicada.**

## LEITURA HONESTA

- **W1 é real mas PEQUENO.** A estrutura é amortizada ~K×, mas para camadas pesadas em valor ela é fração mínima do total → o ganho total fica em ~1,1×. Compartilhar a moldura sozinha não move a agulha.
- **W2: Shannon manda.** O wafer não comprime conteúdo independente. O payload é idêntico à soma. Quem promete 'K datasets de graça' erra — só a moldura é partilhada.
- **W3: desalinhado perde feio (0,32×).** Sem bordas comuns, a união super-subdivide; o wafer fica MUITO pior que arquivos separados. E a foto real (C) também perde (0,67×): RGB + lum + seg não subdividem nos mesmos lugares sob threshold, então a união arrasta todas para baixo.
- **O verdadeiro lever é CORRELAÇÃO entre-camadas, não estrutura.** Shannon proíbe partilhar conteúdo INDEPENDENTE — mas camadas co-registradas de IA são CORRELACIONADAS (profundidade prevê-se de RGB; segmentação, de ambas). Guardar camada 2..K como DELTA/predição sobre a camada 1 partilharia a INFORMAÇÃO MÚTUA — aí sim o ganho é grande. Este MVP partilha só estrutura e por isso mede pequeno: delimita que o wafer ingênuo é fraco e aponta onde o ganho mora (predição entre-camadas).
