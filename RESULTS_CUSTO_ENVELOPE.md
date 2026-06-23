# CUSTO DO ENVELOPE — quanto custa a estrutura EXPLÍCITA?

Decomposição dos bytes do codec BH real vs JPEG, por categoria. Threshold BH=16; JPEG na qualidade que casa o PSNR.


## gradiente (puro)  (PSNR ~59 dB)

| categoria | BH | JPEG |
|---|---|---|
| framing | 100 B | 623 B (inclui regras globais DQT/DHT/SOF) |
| **estrutura explícita** (regra local + hierarquia) | **0 B** | 0 B (sem regra local) |
| resíduo (payload) | 12 B | 21.9 KB |
| **total** | **112 B** | **22.5 KB** |
| estrutura como % do total BH | **0%** | — |
| resíduo BH / resíduo JPEG | **0.0×** | — |

## UI/diagrama (estruturado)  (PSNR ~44 dB)

| categoria | BH | JPEG |
|---|---|---|
| framing | 100 B | 623 B (inclui regras globais DQT/DHT/SOF) |
| **estrutura explícita** (regra local + hierarquia) | **1.9 KB** | 0 B (sem regra local) |
| resíduo (payload) | 29.0 KB | 18.0 KB |
| **total** | **31.0 KB** | **18.7 KB** |
| estrutura como % do total BH | **6%** | — |
| resíduo BH / resíduo JPEG | **1.6×** | — |

## foto natural (perceptual)  (PSNR ~37 dB)

| categoria | BH | JPEG |
|---|---|---|
| framing | 100 B | 623 B (inclui regras globais DQT/DHT/SOF) |
| **estrutura explícita** (regra local + hierarquia) | **8.9 KB** | 0 B (sem regra local) |
| resíduo (payload) | 244.1 KB | 56.3 KB |
| **total** | **253.1 KB** | **56.9 KB** |
| estrutura como % do total BH | **4%** | — |
| resíduo BH / resíduo JPEG | **4.3×** | — |

## A RESPOSTA À PERGUNTA MATADORA

- **A estrutura explícita NÃO é o problema.** Nos três casos, os bytes de 'regra local + hierarquia' são uma fração PEQUENA do total (single dígitos a ~baixas dezenas de %). O 'cabeçalho inteligente' do BH é barato — a posição codifica a hierarquia de graça, e o tipo do nó é ~1-2 bytes.
- **O problema é o RESÍDUO, não a estrutura.** O resíduo do BH é muitíssimo maior que o do JPEG — porque o JPEG ENTROPY-CODIFICA o resíduo (Huffman/aritmético) e o BH o guarda quase cru. O custo não está em tornar a estrutura explícita; está em NÃO comprimir o payload que sobra.
- **Reformulando a tese, agora com número:** o medo do GPT (header inteligente > economia) NÃO se confirma — o header é barato. A derrota do BH-codec vem de outro lugar: falta o entropy coding do resíduo. Logo, a estrutura explícita PAGA por si onde a regra local encolhe o resíduo o suficiente (gradiente/estruturado puro); e PERDE onde o resíduo é denso e precisa de entropy coding (foto).
- **A consequência para o `.bh`:** a estrutura explícita é viável e barata. O que falta para competir em IMAGEM é a maquinaria de compressão do resíduo — que é justamente o que tornaria o `.bh` um codec normal. Logo o valor do `.bh` não é o resíduo (perde para codecs); é a ESTRUTURA EXPLÍCITA barata + as MÚLTIPLAS LEITURAS — que só rendem onde a estrutura importa mais que a textura.
