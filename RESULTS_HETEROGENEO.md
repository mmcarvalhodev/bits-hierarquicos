# REFATORAÇÃO ADAPTATIVA vs BASE-FIXA — varredura por fração de foto

Imagem 1024×1024, threshold BH=16. Esquerda estruturada (plano+gradiente+texto), direita foto natural. Mede BH/WebP a PSNR igual conforme a foto cresce.

| % foto | BH (KB) | PSNR | WebP (KB) | BH/WebP | veredicto |
|---|---|---|---|---|---|
| 0% | 98.9 | 47.0 | 9.2 | **10.75×** | perde |
| 10% | 137.7 | 43.9 | 13.4 | **10.24×** | perde |
| 25% | 207.8 | 41.5 | 20.5 | **10.14×** | perde |
| 50% | 396.2 | 38.9 | 44.5 | **8.90×** | perde |
| 75% | 638.2 | 37.4 | 76.4 | **8.35×** | perde |
| 100% | 842.5 | 36.3 | 102.9 | **8.19×** | perde |

## LEITURA HONESTA (o número refutou a hipótese)

- **O BH PERDE em TODAS as frações — inclusive a 0% de foto** (estruturado puro: 10.7× pior que o WebP). Não há cruzamento. A hipótese 'refatorar-com-regra-adaptativa ganha no heterogêneo' está REFUTADA.
- **Por quê (o diagnóstico):** (1) a parte de TEXTO/UI explode a quadtree — cada borda nítida subdivide em folhas minúsculas, e o BH incha; (2) o ENTROPY CODING do WebP — que o BH não tem — já torna plano, texto e gradiente quase grátis, então NÃO existe o 'desperdício de base fixa' que imaginámos recuperar; (3) o entropy coding é o componente mais importante de um codec, e o BH não o tem.
- **O 48× no gradiente era um canto, não a regra.** Aquele ganho foi num gradiente liso PURO — o caso ideal único da rampa. Bastou pôr texto/UI (estrutura real) para a quadtree explodir e o WebP vencer em tudo.
- **A meta-conclusão honesta:** o CODEC é o pior campo para testar a tese da refatoração. Codec de imagem é máximamente entrincheirado, dependente de entropy coding, e o dado é PERCEPTUAL (o menos composicional que existe). A tese 'payload enxuto + regras explícitas' está certa em princípio (o JPEG a prova), mas para VENCER ali é preciso a maquinaria de entropy — e ter essa maquinaria = virar um codec normal. Testámos a tese, de novo, no seu pior terreno: imagem perceptual.
- **O lar da refatoração-composicional NÃO é imagem** — é dado SIMBÓLICO/estruturado onde a composição é explícita e não há jogo de entropy-coding-de-pixels a perder. Volta ao mesmo lugar: Intent AI, não codec.
