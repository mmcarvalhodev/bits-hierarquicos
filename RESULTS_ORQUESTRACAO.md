# ORQUESTRAÇÃO — BH roteia codec especialista por região

Imagens 512×512. A=WebP no todo · B=soma WebP/região · C=orquestrado (especialista/região). Dois conteúdos: um dominado por foto, outro por formas-fechadas (documento).

| conteúdo | A WebP-todo | B split-WebP | C orquestrado | C vs A |
|---|---|---|---|---|
| foto-pesado (plano+grad+UI+FOTO) | 11.5 KB | 12.6 KB (1.10×) | 11.6 KB | **1.01×** |
| documento (plano+grad+UI+diagrama) | 4.8 KB | 4.6 KB (0.96×) | 2.2 KB | **0.47×** |

## LEITURA HONESTA

- **A orquestração é uma estratégia QUE NÃO PODE PERDER MUITO** — no pior caso ela roteia tudo para o melhor codec único. No conteúdo foto-pesado empata (**1.01×**): a foto domina os BYTES (mesmo sendo 25% da área) e a orquestração usa WebP nela de qualquer forma — não há o que ganhar.
- **No documento (formas-fechadas) ela GANHA (0.47×)** — porque o gradiente vira 12 B (fórmula) e o plano 3 B, onde o WebP os trata como sinal e gasta bytes. O ganho é proporcional à fração dos BYTES que é forma-fechada (plano/gradiente/vetor), não à área.
- **A regra exata:** orquestrar ganha quando o orçamento de bytes é dominado por conteúdo de FORMA FECHADA (documento, diagrama, UI, cena de IA em camadas vetoriais); empata quando é dominado por FOTO (o byte da textura manda, e ali o especialista é o WebP mesmo). Nunca perde feio — só paga o overhead de estrutura.
- **O que o BH adiciona ao PDF:** o PDF já orquestra especialistas num container — mas é uma LISTA plana de objetos. O BH acrescenta HIERARQUIA (pertencimento, níveis) e MÚLTIPLAS LEITURAS (preview/ROI/prova) sobre a mesma estrutura. O resíduo, esse, é delegado — o BH nunca devia comprimi-lo sozinho. A frase do GPT está certa: **o BH orquestra codecs por região dentro de uma hierarquia explícita; não os substitui.**
