# Bits Hierárquicos — Pitch de Apresentação

> **Em uma frase:** é uma estrutura que permite representar um ativo
> heterogêneo, navegar por partes dele sem carregar tudo, e delegar cada
> região ao melhor formato especialista.

---

## SLIDE 1 — O problema

Todo dado hoje te obriga a escolher **um**:

- **Compacto** (JPEG/WebP/AVIF) → mas para ver um pedaço, decodifica tudo.
- **Navegável** (índices, OLAP, vector DB) → mas é estrutura colada por cima,
  em vários sistemas que precisam ser sincronizados.

O dado nasce cru, e o resto do stack gasta tempo, espaço e complexidade
**redescobrindo a estrutura dele** — índices, agregados, previews, caches,
provas, metadados. Tudo espalhado em sistemas separados.

---

## SLIDE 2 — A ideia (não é um codec, nem um banco)

**Bits Hierárquicos (BH)** é um **envelope estrutural**: o dado nasce com a
sua própria estrutura. Em vez de comprimir tudo numa base só, o BH:

```
1. torna a estrutura EXPLÍCITA   — hierarquia, pertencimento, regras (custo: 0–6%)
2. ROTEIA cada região            — foto→WebP, gradiente→fórmula, texto→PNG
3. permite MÚLTIPLAS leituras    — preview / região / agregado / prova
```

> Não substitui codecs. **Orquestra** codecs por região, dentro de uma
> estrutura que sabe o que cada região significa.

---

## SLIDE 3 — A capacidade central

O coração do BH não é "ser menor". É **ler só a parte que você precisa, sem
decodificar o resto** — uma capacidade que nenhum formato compacto tem. O
tamanho é consequência, não a promessa.

| | resultado |
|---|---|
| **Acessar uma região** | **3–55× menos bytes** que o WebP (que decodifica o arquivo TODO para qualquer pedaço) |
| ...e ainda menor | 2,1× menor que o WebP, no mesmo arquivo |
| Custo de tornar a estrutura explícita | apenas 0–6% do arquivo |

> **Capacidade, não benchmark.** "Leio só o ramo que preciso" é uma propriedade
> do formato — não depende de qual documento, de qual dataset, de qual condição.
> É isso que sobrevive ao engenheiro cético. Compacto **E** navegável, num
> arquivo só — hoje isso exige quatro ferramentas.

---

## SLIDE 4 — Por que é diferente

O BH converge para algo que mistura, sem ser nenhum deles:

```
PDF    → orquestração de especialistas
Merkle → hierarquia verificável
OLAP   → leitura seletiva
AST    → estrutura explícita
```

Ninguém vende **representação + leitura + pertencimento + hierarquia +
múltiplas visões** como uma estrutura única. **Esse é o pedaço novo.**

---

## SLIDE 5 — Onde ganha (honesto)

```
GANHA   dado ESTRUTURA-DOMINANTE: documentos, diagramas, UIs, mapas, dados em
        camadas, saídas estruturadas de IA, conhecimento simbólico.
        No limite (dado gerado por regra): o payload vira o PROGRAMA que o
        gera — 800× a 3.600× menor.
DELEGA  sinal denso (foto, áudio, embedding) → WebP/AVIF/HNSW reinam, e o BH
        os CONVOCA. Não compete onde não deve.
```

A fronteira não é a entropia — é o **reconhecimento da estrutura**.

---

## SLIDE 6 — Onde alguém diria "isso é diferente"

```
MEMÓRIA DE AGENTES
   hoje: documentos + embeddings + resumos + cache + índices + metadados,
         tudo espalhado.
   .bh:  um único envelope navegável.

KNOWLEDGE SYSTEMS (Notion/Obsidian/Roam/Logseq)
   hoje: estruturam informação, mas a estrutura NÃO é parte do formato.
   .bh:  a estrutura É o formato.

ATIVOS COMPOSTOS DE IA
   imagem + máscara + profundidade + prompt + versão + metadados.
   hoje: um Frankenstein de sistemas. .bh: nativo.
```

---

## SLIDE 7 — O estado e o pedido

- **Validado por medição**, não por slide: 9 ângulos testados, 128+ testes
  verdes, correção como portão, baselines honestos, autocorreções públicas.
- **A construção começou:** `bhmem` — um `.bh` usável para **memória de
  agente** (biblioteca + testes). O agente lê o resumo / um tópico / uma janela
  / a proveniência sem carregar a memória inteira: **36× / 22× / 9× / 8× menos
  bytes** que um store plano. A tese virou ferramenta.
- **Ainda não é um produto** — é uma arquitetura medida com o primeiro artefato
  executável. O próximo passo é ligar o `bhmem` a um loop de agente real e
  somar a face de proveniência verificável (Merkle sobre os blocos).

---

> **O valor não está no bloco comprimido. Está na estrutura que sabe o que
> aquele bloco significa.**
