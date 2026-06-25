# Bits Hierárquicos — Pitch de Apresentação

> **Numa frase:** um modelo de representação onde múltiplas interpretações —
> possivelmente contraditórias — partilham um substrato imutável e permanecem
> consultáveis, sem duplicar o dado e sem as forçar a uma única verdade.

---

## SLIDE 1 — O problema

> **Não duplicar o mundo toda vez que alguém discorda dele.**

Parte de uma base comum — um dataset, um edifício, um conjunto documental, um
histórico de conversa. Sobre essa base, surgem naturalmente várias
interpretações: anotadores rotulam-na, disciplinas leem-na de forma diferente,
hipóteses competem sobre ela, versões acumulam-se. Elas **coexistem**.

Hoje, segurá-las obriga a uma escolha má:

- **copiar a base** uma vez por interpretação → K leituras custam K cópias do
  mundo; ou
- **fundir numa só** → uma representação dominante vence e o resto perde-se.

---

## SLIDE 2 — A ideia (um modelo, não um formato)

> **BH é um modelo de representação para substratos imutáveis partilhados e
> interpretações concorrentes.**

Um substrato, guardado uma vez e imutável. Cada interpretação é uma **entidade
de 1ª classe, co-registada** sobre ele. O leitor escolhe a lente no momento da
leitura — a adjudicação é diferida e opcional, nunca embutida.

```
SUBSTRATO     guardado uma vez, imutável, partilhado por toda leitura
CAMADAS       cada interpretação é entidade de 1ª classe, co-registada
LEITURAS      uma lente / a matriz / a maioria / a discordância
              — tua escolha, no momento da leitura, não embutida
```

Damos a esta propriedade um **nome de trabalho — a First-Class Interpretation
Representation (FCIR)**: interpretações mantidas como entidades persistentes,
endereçáveis e de *primeira classe* sobre um substrato partilhado, em vez de
versões temporárias ou conflitos a resolver. *(Nome de trabalho — ver Slide 4.)*

---

## SLIDE 3 — O teste distintivo (falsificável)

> Dadas duas interpretações que **discordam** sobre o mesmo elemento — podem
> **ambas permanecer**, nenhuma marcada como errada, até alguém escolher (ou
> recusar) adjudicar?

Muitos sistemas acabam por **convergir para uma representação dominante**, ou por
**isolar cada interpretação numa cópia/versão independente**. O BH mantém-nas
co-registadas sobre um substrato e deixa a adjudicação esperar. É esse o
diferencial — enunciado como um teste que se corre em qualquer sistema, não como
gabarolice.

---

## SLIDE 4 — O que NÃO somos (o posicionamento honesto)

Varremos 20 domínios de dados. O resultado matou a alegação fácil de que "o BH é
universalmente novo":

> **Guardar o substrato uma vez + ler seletivo já é SOTA maduro** — DICOM,
> COG/STAC, lakeFS, CRAM/tabix, S-LoRA, MAM. O BH **não** afirma inventar isso.

A nossa varredura de 20 domínios **identificou a First-Class Interpretation
Representation (FCIR)** — manter leituras rivais como entidades preservadas em
vez de as resolver — como a propriedade que melhor distingue o BH **das
abordagens avaliadas**. É um resultado da investigação, não uma verdade
universal; FCIR é um nome de trabalho, e a propriedade pode vir a revelar-se mais
ampla. Dizer com clareza o que o BH **não** é — e até onde a afirmação alcança —
é o que sobrevive ao engenheiro cético.

---

## SLIDE 5 — Onde serve, e onde não (o limite útil)

```
SERVE     várias leituras de UM objeto-base:
          · anotação com anotadores que discordam
          · memória de agente com versões conflitantes sobre um histórico
          · BIM/CAD — disciplinas a ler um edifício (não cinco cópias)
          · legal / eDiscovery — leituras rivais de um conjunto documental
          · ciência — hipóteses concorrentes sobre o mesmo dado bruto

NÃO SERVE  sinal denso (foto / áudio / embeddings) → delega a codecs
           objetivos de verdade-única (consenso, gold labels) → já resolvido
```

Um pitch que enuncia o seu próprio limite é o oposto de vapor.

---

## SLIDE 6 — A evidência (o princípio é reprodutível)

O mesmo modelo apareceu — de forma independente — em quatro domínios
completamente diferentes. Essa **reprodutibilidade** vale mais do que qualquer
número isolado:

| instância | domínio | o mesmo modelo, instanciado |
|---|---|---|
| `bhanno` | anotações rivais | a mais pura: K rotulagens coexistem, adjudicação opcional |
| `bhmem` | memória de agente | versões conflitantes sobre um histórico |
| `bhckpt` | checkpoints de modelo | leituras alternativas de uma base partilhada |
| `bhtrace` | traces | lentes concorrentes sobre uma árvore de spans |

Um princípio, quatro instâncias, cada uma medida e testada — correção como
portão, baselines honestos, autocorreções públicas, um DOI no Zenodo. Os números
existem (4,6×, 35×, 1 779×, 9×); o ponto é que o **princípio se manteve as quatro
vezes**.

---

## SLIDE 7 — O estado e o pedido

- **É um princípio com instâncias medidas**, não um produto acabado. A varredura
  encontrou o seu **limite útil** — e um limite útil é onde um produto sério
  começa; sem limite, vira religião.
- **A pergunta seguinte é produto, não novidade:** dos domínios onde serve, qual
  é a primeira semente a construir a sério?

---

> **Não duplicar o mundo toda vez que alguém discorda dele.**
