# BH MERKLE MVP — RESULTADOS

Dataset: 1,048,576 itens de 64 B · SHA-256 · árvore binária.
Métrica primária: **bytes lidos/transmitidos** para a tarefa (o análogo do bytes-lidos do codec e linhas-lidas do banco).

## VEREDICTO POR ALEGAÇÃO

- **M1 (commitment O(1) ≈ thumbnail): CONFIRMADA** — a integridade de 1,048,576 itens cabe em 32 bytes (1 hash).
- **M2 (prova O(log n) ≈ ROI): CONFIRMADA** — provar pertença custa 20 hashes (644 B); ingênuo: 33,554,432 B. Ganho 52,103×.
- **M3 (localizar adulteração O(log n) ≈ diff): CONFIRMADA** — achou o item adulterado lendo 40 nós; re-hash total leria 1,048,576. Ganho 26,214×.
- **Borda (declarada): auditar TODOS lê tudo; árvore ~dobra o armazenamento de hashes; Merkle dá integridade, não sigilo.**

## TAREFAS — trabalho medido

| tarefa | BH lê | baseline ingênuo | ganho |
|---|---|---|---|
| Commitment do dataset | 32 B | 33,554,432 B (hash por item) | 1,048,576× |
| Prova de pertença | 644 B | 33,554,432 B (os N itens) | 52,103× |
| Multiprova 32 itens contíguos | 728 B | 20,608 B (32 provas separadas) | 28.3× |
| Localizar adulteração | 40 nós | 1,048,576 re-hashes | 26,214× |

## ESCALA — a prova cresce com log n, não com n

| N | níveis | prova (hashes) | prova (bytes) | ingênuo (bytes) | ganho |
|---|---|---|---|---|---|
| 1,024 | 10 | 10 | 324 | 32,768 | 101× |
| 4,096 | 12 | 12 | 388 | 131,072 | 338× |
| 16,384 | 14 | 14 | 452 | 524,288 | 1,160× |
| 65,536 | 16 | 16 | 516 | 2,097,152 | 4,064× |
| 262,144 | 18 | 18 | 580 | 8,388,608 | 14,463× |
| 1,048,576 | 20 | 20 | 644 | 33,554,432 | 52,103× |

## A MESMA ÁRVORE, CINCO LEITURAS

Nenhuma estrutura auxiliar. A MESMA árvore respondeu:
- **commitment** — lê só a raiz (1 hash);
- **prova de pertença** — lê um ramo (log n irmãos);
- **multiprova** — várias folhas compartilham irmãos comuns;
- **localizar adulteração** — desce o ramo divergente (log n);
- **auditoria total** — lê todas as folhas (o baseline interno).
Uma estrutura, várias interpretações — a leitura é escolhida pelo objetivo. Igual ao codec (thumbnail/ROI/full) e ao banco (agregado/poda/scan). É a tese, num terceiro terreno.

## LEITURA HONESTA

- **M1/M2/M3 ganham por construção** — o agregado-hash vive nos nós; a hierarquia dá prova e localização logarítmicas. Mesma origem do ganho do thumbnail (codec) e da agregação (banco).
- **A borda é a mesma das outras** — verificar TUDO lê tudo (sem atalho), como decodar o 4K inteiro ou agregar sem range. O ganho é em acesso/prova SELETIVOS, não em trabalho total.
- **Não inventa cripto** — Merkle é padrão (blockchain, git, CT). O PoC prova a UNIFICAÇÃO: verificar-por-Merkle é a mesma leitura-por-objetivo-sobre-hierarquia-grátis dos outros dois terrenos.
