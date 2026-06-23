# Bits Hierárquicos — Pitch

## O problema

Todo formato de dado te obriga a escolher **um**:

- **Compacto** (JPEG, WebP, AVIF) — mas para ver um pedaço, decodifica tudo.
- **Navegável** (índices, OLAP, vector DB) — mas é estrutura colada por cima,
  em vários sistemas que precisam ser sincronizados.

O dado nasce cru e burro, e o resto do stack gasta tempo, espaço e complexidade
**redescobrindo a estrutura dele** — índices, agregados, previews, caches, provas.

## A ideia

**Bits Hierárquicos (BH)** é um envelope estrutural onde o dado já nasce com a
sua estrutura. Em vez de comprimir tudo numa base só, o BH **roteia cada região
ao melhor especialista** (foto→WebP, gradiente→fórmula, texto→PNG, vetor→equação)
**dentro de uma hierarquia explícita** que serve de índice.

> Não substitui codecs. Orquestra codecs por região, dentro de uma estrutura
> que sabe o que cada região significa.

## A prova (medido)

Um documento como `.bh`, num arquivo só:

- **2,1× menor** que o WebP (cada região no formato que lhe convém);
- **e** lê qualquer região por **3 a 55× menos bytes** — sem decodificar o todo.

Compacto **E** navegável. Hoje isso exige quatro ferramentas separadas; o `.bh`
faz numa estrutura.

```
WebP/AVIF → ótimo, mas leitura única
PDF       → orquestra, mas lista plana, sem leitura seletiva
OLAP/GPU  → leitura seletiva, mas não é formato
.bh       → as duas + hierarquia + pertencimento, num envelope
```

## Onde ganha (honesto)

Conteúdo **estrutura-dominante**: documentos, diagramas, UIs, mapas, dados em
camadas, **saídas multimodais de IA** (RGB + profundidade + segmentação +
embeddings da mesma cena), dados simbólicos. Em foto pura, o WebP reina — e o
BH simplesmente o convoca lá.

## Por que agora

A IA passou a **gerar** dados estruturados em camadas co-registradas — o caso
exato onde guardar tudo num envelope hierárquico, navegável e auto-descritivo
vale mais que comprimir um sinal cru. Ninguém tem um formato que una
representação + leitura seletiva + pertencimento. O BH é esse formato.

## O pedido

Não é um produto pronto — é uma tese **medida e validada** pronta para virar
construção. O próximo passo é o `.bh` nativo num domínio greenfield que já
precisa dele: armazenamento estrutural para saídas de IA / um substrato
composicional de conhecimento. Estrutura explícita, pertencimento, e múltiplas
leituras sobre a mesma realidade — o que nenhum formato atual tentou oferecer.

---

*O valor não está no bloco comprimido. Está na estrutura que sabe o que aquele
bloco significa.*
