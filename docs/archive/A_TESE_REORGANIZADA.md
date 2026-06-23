# BITS HIERÁRQUICOS — A TESE, REORGANIZADA
## Onde o BH sobrevive ao escrutínio: não como codec, mas como estrutura

**Autores:** Márcio M. Carvalho (formulação) · investigação medida em colaboração
**Data:** Junho 2026
**Natureza:** o pouso da campanha — a formulação onde o BH ganha pelo motivo certo

---

## 0. A MUDANÇA DE PERGUNTA (o resultado real da campanha)

A campanha começou perguntando **"o BH é um codec?"** e a resposta foi ficando,
medição após medição, **"não".** A pergunta certa, que só emergiu no fim, é
outra:

```
ERRADA:  "O BH comprime melhor que JPEG/WebP/AVIF?"           → não.
CERTA:   "O BH é um orquestrador estrutural de representações?" → sim.
```

E com a pergunta certa, os resultados de toda a campanha param de parecer
derrotas e passam a fazer sentido.

---

## 1. A SEPARAÇÃO QUE RESOLVE TUDO

```
PROBLEMA DO RESÍDUO  ≠  PROBLEMA DO PARADIGMA
```

Metade da investigação misturou as duas. "BH-compressor" (tentar comprimir o
resíduo sozinho) perde — mas isso é o resíduo, não o paradigma. O paradigma é
estrutura explícita + pertencimento + leituras. Separadas, cada uma tem seu
veredicto honesto:

| | o que é | resultado medido |
|---|---|---|
| **BH-compressor** | competir com JPEG/WebP/AVIF no resíduo | **perde** (foto 4-10×; empata só em gradiente puro) |
| **BH-orquestrador** | estrutura explícita + roteia resíduo ao especialista | **ganha pelo motivo certo** (documento 2,1× vs WebP) |

A consequência: o resíduo **delega-se** ao especialista local. O BH nunca
devia comprimi-lo. WebP/AVIF reinam na textura — e o BH os *convoca* lá.

---

## 2. A PERGUNTA MATADORA, RESPONDIDA

> "Quanto custa tornar a estrutura explícita?"

O medo: estrutura + hierarquia + envelopes + regras + pertencimento = explosão
de overhead. A medição (codec real, decomposição por categoria):

```
estrutura explícita = 0% a 6% do total (medido em 3 imagens)
```

**Muito menos do que se temia.** A posição codifica a hierarquia de graça; o
tipo do nó são ~2 bits. O cabeçalho inteligente é barato. O caro nunca foi a
estrutura — era o resíduo cru (sem entropy coding), que agora se delega.

---

## 3. O GANHO PELO MOTIVO CERTO (e por que é diferente dos anteriores)

```
Ganhos ANTERIORES (GPU 1.750×, banco 488×, Merkle 52.000×):
   grandes, mas vs baseline INGÊNUO. Mecanismo (resumo pré-computado na
   hierarquia) já é SOTA — materialized views, zone-maps, OLAP, Merkle.
   O BH captura corretamente um valor que o mundo já captura.

Ganho da ORQUESTRAÇÃO (documento 2,1× vs WebP):
   menor, mas vs o ESTADO DA ARTE, por uma propriedade ARQUITETURAL —
   usar a representação certa para cada região. Primeira vitória que não
   vem de comparar contra algo ingênuo.
```

**A regra medida:** orquestrar ganha quando o orçamento de bytes é dominado
por conteúdo de **forma fechada** (plano, gradiente, vetor, texto) — documento,
diagrama, UI, cena de IA em camadas. Empata quando dominado por **foto** (o
byte da textura manda, e ali o especialista é o WebP). **Nunca perde feio** —
é uma estratégia que, no pior caso, roteia tudo para o melhor codec único.

---

## 4. AS DUAS FACES (e onde a GPU encaixa)

O `.bh` carrega DUAS faces que nenhuma ferramenta SOTA dá juntas:

```
FACE DE LEITURA (resumo no nó → ler seletivamente é barato)
   provada pela GPU (1.750× real), banco, Merkle, thumbnail/ROI.
   preview / região / agregado / prova SEM decodificar tudo.

FACE DE REPRESENTAÇÃO (estrutura explícita + resíduo delegado)
   provada pela orquestração (2,1× em documento).
   a representação certa por região.

   WebP/AVIF → resíduo ótimo, leitura ÚNICA
   PDF       → orquestra especialistas, mas LISTA plana, sem leitura seletiva
   OLAP/GPU  → leitura seletiva, mas não é formato de representação
   .bh       → as DUAS faces + hierarquia, num envelope só
```

A GPU não foi um beco: é a **prova em silício** de que a face de leitura é real
e rápida. Junto da orquestração (representação), formam a proposta inteira.

---

## 5. OS TRÊS LUGARES ONDE O BH SOBREVIVE — uma raiz, três escalas

```
1. BH como FORMATO ESTRUTURAL          (um ativo)
2. BH como ORQUESTRADOR de representações (um ativo heterogêneo)
3. BH como SUBSTRATO COMPOSICIONAL do Intent (um sistema simbólico inteiro)
```

Raiz comum: **estrutura > sinal.** Nenhum dos três vence os incumbentes no
jogo deles. Os três oferecem o que os incumbentes nunca tentaram: estrutura
explícita, pertencimento, e múltiplas formas de leitura sobre a mesma
realidade. O valor não está no bloco comprimido — está na **estrutura que sabe
o que aquele bloco significa.**

---

## 6. AS FRONTEIRAS HONESTAS (para a tese não virar fé)

```
- "Ganha pelo motivo certo" ≠ "achámos o produto". É validação CIENTÍFICA;
  o produto ainda exige adoção + greenfield (a construção, não o benchmark).
- O orquestrador compete com o PDF (incumbente), não com o WebP. Seu
  diferencial — hierarquia + leituras múltiplas — é real mas NÃO-PROVADO
  como necessidade de mercado.
- O valor do BH (estrutura/pertencimento/leituras) é ARQUITETURAL — não se
  prova em benchmark; prova-se construindo e operando.
- A face de leitura tem números enormes (1.750×) mas vs o INGÊNUO; vs o SOTA,
  empata (a técnica já existe). O diferencial é a UNIÃO das faces, não um número.
- A casa do paradigma é dado ESTRUTURA-DOMINANTE; em foto/áudio/sinal denso
  o conexionismo reina, e o BH os delega — não os enfrenta.
```

---

## 7. A IRONIA QUE FECHA O ARCO

O BH foi discutido como bit, árvore, codec, banco, GPU. E acaba chegando
exatamente onde o documento de Dezembro de 2025 sempre apontou: **contexto,
pertencimento, hierarquia e múltiplas leituras.** A campanha não descobriu um
codec melhor; descobriu que o BH nunca foi um codec — é a **estrutura que
carrega o significado do dado**, para que o sistema não precise redescobri-lo
depois. Testá-lo como compressor foi testá-lo fora de casa seis vezes. Em
casa — estrutura, orquestração, Intent — ele ganha pelo motivo certo.

---

*Reprodução das medições: `RESULTS_ORQUESTRACAO.md` (2,1× documento),
`RESULTS_CUSTO_ENVELOPE.md` (estrutura 0-6%), `RESULTS_HETEROGENEO.md`
(BH-compressor perde), `gpu/RESULTS_REAL_GPU.md` (1.750× face de leitura),
`compositional/RESULTS_COMPOSICIONAL.md` (substrato simbólico).*
