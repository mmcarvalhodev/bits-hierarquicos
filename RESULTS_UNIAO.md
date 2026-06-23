# A UNIÃO — representação + leitura seletiva no mesmo .bh

Documento 512×512: 4 regiões de naturezas diferentes. O .bh roteia cada resíduo ao especialista E mantém a estrutura para leitura seletiva.

## FACE 1 — Representação (tamanho)

| | tamanho |
|---|---|
| WebP no todo | 4.8 KB |
| .bh orquestrado | 2.3 KB |
| **ganho** | **2.09× menor** |

### Onde os bytes do .bh foram

| região | especialista | bytes |
|---|---|---|
| (estrutura) | árvore+bounds+ids | 84 B |
| plano | constante | 3 B |
| gradiente | fórmula | 12 B |
| texto/UI | WebP | 506 B |
| diagrama | PNG | 1.7 KB |

## FACE 2 — Leitura seletiva (bytes para ler UMA região)

No .bh, ler uma região = estrutura + o payload dela. No WebP, qualquer região exige decodificar o arquivo TODO.

| operação | .bh lê | WebP lê | .bh vs WebP |
|---|---|---|---|
| ler região 'plano' | 87 B | 4.8 KB (tudo) | **55× menos** |
| ler região 'gradiente' | 96 B | 4.8 KB (tudo) | **50× menos** |
| ler região 'texto/UI' | 590 B | 4.8 KB (tudo) | **8× menos** |
| ler região 'diagrama' | 1.8 KB | 4.8 KB (tudo) | **3× menos** |
| preview (formas-fechadas renderizam grátis) | ~99 B+ | 4.8 KB (tudo) | **muito menos** |

## A UNIÃO, EM UMA FRASE

- **O mesmo arquivo é 2.1× menor que o WebP E permite ler qualquer região por ~dezenas× menos bytes** — porque a estrutura é o índice e o resíduo é delegado. O WebP é menor-é-único: para um preview ou uma região, decodifica tudo.
- **Nenhuma ferramenta SOTA dá as duas juntas:** WebP/AVIF = resíduo ótimo mas leitura única; PDF = orquestra mas lista plana sem leitura seletiva; OLAP/GPU = leitura seletiva mas não é formato. O `.bh` = as duas + hierarquia, num envelope.
- **Honestidade:** vale em conteúdo ESTRUTURA-DOMINANTE (documento/diagrama/UI). Em foto pura, a representação empata (WebP reina na textura) e só sobra a face de leitura. E é arquitetura, não benchmark: a prova final é construir o formato, não medir o protótipo.
