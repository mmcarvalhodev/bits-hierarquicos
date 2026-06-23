# DECODE-PROGRAMA — teste rigoroso (generalidade + ruído + custo escondido)

## (1) Generalidade — várias famílias geradas por regra

| família | WebP | programa | programa vs WebP |
|---|---|---|---|
| anéis | 37.8 KB | 13 B | **2,904× menor** |
| ondas | 46.4 KB | 13 B | **3,572× menor** |
| xadrez | 2.4 KB | 3 B | **809× menor** |
| gradiente | 2.1 KB | 1 B | **2,096× menor** |

## (2) Ruído — base procedural + ruído α (o caso real)

`programa-aware` = programa (13 B) + WebP(resíduo). `WebP-todo` = WebP(tudo).

| α (ruído) | WebP-todo | programa-aware | vence? | PSNR p-aware |
|---|---|---|---|---|
| 0.00 | 37.8 KB | 537 B | SIM | inf dB |
| 0.05 | 91.6 KB | 73.2 KB | SIM | inf dB |
| 0.10 | 124.6 KB | 112.0 KB | SIM | inf dB |
| 0.25 | 165.3 KB | 159.4 KB | SIM | inf dB |
| 0.50 | 205.5 KB | 202.1 KB | SIM | inf dB |
| 1.00 | 238.7 KB | 223.1 KB | SIM | 19 dB |

## LEITURA HONESTA

- **(1) Generaliza — não é cherry-pick.** Anéis, ondas, xadrez, gradiente: o programa bate o WebP por ordens de grandeza em TODAS. Onde o dado é gerado por regra, o programa-no-cabeçalho esmaga, sempre.
- **(2) Sob ruído, o programa-aware MANTÉM a vantagem da estrutura.** Mesmo com ruído alto, subtrair a base conhecida deixa só o resíduo — e o WebP-todo ainda paga pela estrutura que não sabe separar. O programa-aware ganha pelo CUSTO DA ESTRUTURA que removeu. A vitória persiste; encolhe, não some.
- **(3) O CUSTO ESCONDIDO — e é o que importa de verdade:** o exemplo assume que SE CONHECE a regra (anéis = 5 params). Para dado arbitrário, DESCOBRIR o programa que o gera é o problema inverso — **trivial quando se conhece a família, mas indecidível em geral** (a complexidade de Kolmogorov é incomputável). O encoder de verdade teria que FAZER síntese de programa / regressão simbólica. É aí que mora a dificuldade, não no ruído.
- **A conclusão para o BH:** 'decode-programa no cabeçalho' é real e poderoso para dado de FAMÍLIA CONHECIDA (fórmulas, formas, regras, primitivos do Intent). Não é mágica universal: exige um catálogo de regras reconhecíveis. O BH seria o formato que carrega o programa + delega o resíduo. A fronteira não é a entropia do resíduo — é o reconhecimento da estrutura.
