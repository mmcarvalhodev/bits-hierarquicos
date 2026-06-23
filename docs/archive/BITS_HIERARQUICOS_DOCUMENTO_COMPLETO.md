# BITS HIERÁRQUICOS — DOCUMENTO COMPLETO
## Uma forma diferente de ler dados, provada em quatro terrenos

**Autor:** Márcio M. Carvalho
**Data:** Junho 2026
**Origem conceitual:** `arquitetura_bits_hierarquicos.md` (Dezembro 2025)
**Natureza:** documento explicativo — a ideia, os experimentos, os limites

---

## ÍNDICE

1. A ideia em uma frase
2. O princípio, com cuidado
3. Por que isto não é "mais um algoritmo"
4. Os cinco terrenos
   - 4.1 Codec de imagem (ler para compactar)
   - 4.2 Banco de dados (ler para consultar)
   - 4.3 Verificação / Merkle (ler para provar)
   - 4.4 Wafer (múltiplas camadas no mesmo dado)
   - 4.5 GPU (movimento de dados, em silício real)
5. As leis que emergiram
6. A prova de escala: o filme
7. O que isto NÃO é (honestidade)
8. Onde isto vale de verdade (aplicações)
9. Como reproduzir
10. Conclusão

---

## 1. A IDEIA EM UMA FRASE

```
Um dado não tem um significado fixo. Tem o significado que a convenção de
leitura lhe dá. A hierarquia — a estrutura — não está gravada nos bits;
está no acordo sobre como lê-los. Logo, ela pode custar zero, e os mesmos
bytes podem servir a muitos objetivos diferentes.
```

O ponto de partida, do documento original de Dezembro de 2025: **o byte já é
uma árvore binária implícita.** A letra 'a' (ASCII 97 = `01100001`) pode ser
lida como oito bits soltos, ou como uma árvore de decisões por níveis. Os
bits são os mesmos; o que muda é a *interpretação*. Bits Hierárquicos apenas
tornam essa interpretação explícita e a usam de propósito.

---

## 2. O PRINCÍPIO, COM CUIDADO

Três afirmações precisas sustentam tudo o que segue.

**(a) A hierarquia é grátis quando a posição a codifica.**
Se os dados são gravados numa ordem conhecida (por exemplo, varrendo uma
árvore nível a nível), então a posição de cada elemento no fluxo *já diz* a
que nível e a que ramo ele pertence. Não é preciso gravar "este é o nó 3 do
nível 2" — isso se deduz de *onde* o byte está. O custo da estrutura, nesse
caso, é zero.

**(b) Os mesmos bytes, lidos por convenções diferentes, respondem perguntas
diferentes — sem transformação.**
Se a estrutura carrega, em cada nó, um *resumo* do que está abaixo dele
(uma cor média, um mínimo e um máximo, um hash), então:
- ler só o topo dá uma resposta grosseira e barata;
- ler um ramo dá uma resposta local;
- ler tudo dá a resposta completa.
São leituras diferentes do mesmo dado, escolhidas pelo objetivo.

**(c) Não existe "melhor interpretação" em abstrato — só para um objetivo.**
A leitura certa para comprimir não é a mesma que para consultar, nem para
provar. O valor do paradigma é ter uma moldura onde várias interpretações
coexistem, e escolher a que rende para a operação em mãos.

---

## 3. POR QUE ISTO NÃO É "MAIS UM ALGORITMO"

Um algoritmo resolve um problema. Bits Hierárquicos é anterior a isso: é uma
*maneira de organizar e ler* dados, da qual muitos algoritmos podem nascer.

A prova dessa generalidade não pode vir de um só domínio — qualquer ideia
parece boa no exemplo que a inspirou. Por isso a mesma moldura foi levada a
**quatro terrenos que não conversam entre si**. Se ela rende nos quatro,
deixa de ser um truque de um caso e passa a ser um princípio.

A disciplina, em todos: **declarar antes de medir** onde a ideia deveria
ganhar E onde deveria perder, e então medir — reportando os dois. Nenhum
número foi prometido antes da medição. A correção (a leitura bate com a
verdade) foi sempre o portão antes de qualquer comparação de desempenho.

---

## 4. OS CINCO TERRENOS

### 4.1 CODEC DE IMAGEM — ler para compactar

**A leitura:** uma imagem é dividida recursivamente em quadrantes (uma
*quadtree*). Cada nó guarda um resumo (a cor média do seu quadrante). Onde a
imagem é uniforme, o ramo termina cedo; onde tem detalhe, subdivide.

**O que isso dá de graça:**
- *thumbnail* = ler só os primeiros níveis (o topo da árvore);
- *região (ROI)* = ler só um ramo;
- *imagem completa* = ler tudo.
O mesmo arquivo é todas as resoluções — a resolução é *quanto* dele você leu.

**O resultado medido (head-to-head contra PNG/JPEG/WebP):**
- Em conteúdo que casa com a interpretação (um gradiente), o codec — tosco,
  em Python — ficou **48× menor que o WebP, com qualidade maior.** Não por
  engenharia, mas porque a interpretação certa (uma "rampa" de 4 cantos) *é*
  o gradiente, enquanto o WebP gasta centenas de KB descrevendo-o.
- Em *acesso*, ganhou de todos: gerar um thumbnail de uma foto 4K leu **4×
  menos** que o WebP, **44× menos** que o PNG — porque um codec polido
  precisa do arquivo quase inteiro para um preview, e o BH não.

**A fronteira honesta:** em compressão de *foto natural*, os codecs polidos
vencem. A textura de folhas e pele precisa de decomposição em frequência
(DCT) + quantização + entropy coding — décadas de engenharia. Adicionámos
uma interpretação DCT e medimos: ela *funciona* (corta 40–66%), mas não
fecha o gap, porque falta a quantização/entropy. E aí está a lição: quando
preencher a lacuna exige reconstruir o JPEG, o valor único do BH deixa de
ser "comprime melhor" e volta a ser *hierarquia grátis + acesso seletivo*.

### 4.2 BANCO DE DADOS — ler para consultar

**A leitura:** uma tabela ordenada é coberta por uma árvore de agregação.
Cada nó guarda min/max/soma/contagem do seu pedaço. É o análogo 1D da
pirâmide do codec — mesmo princípio, dado diferente.

**As três leituras da mesma árvore:**
- *agregação* (SUM, COUNT, MIN, MAX) = ler os nós-resumo, não as linhas;
- *filtro com poda* = saltar subárvores que o min/max exclui;
- *varredura* = ler tudo.

**O resultado medido (1.000.000 de linhas, métrica = linhas lidas):**
- SUM global: **0 linhas** lidas (só a raiz) vs 1.000.000 — ganho infinito.
- SUM de um intervalo de 10%: **1.564** vs 99.868 — 64×.
- Filtro seletivo no eixo organizado: **488×** menos linhas.

**A fronteira honesta:** filtrar por um valor que não tem relação com a
ordem da tabela (ou por uma coluna que a árvore não resume) não poda nada —
lê tudo. *Mas* essa perda vira ganho ao materializar a interpretação certa:
guardar um contador por categoria em cada nó transformou um filtro que lia
1.000.000 de linhas numa leitura de **0**. O custo: armazenamento, que
escala com a cardinalidade. É exatamente o que bancos reais fazem com
índices — não se indexa tudo; escolhe-se.

### 4.3 VERIFICAÇÃO / MERKLE — ler para provar

**A leitura:** a mesma árvore, mas o resumo de cada nó é um *hash* dos
filhos. É uma árvore de Merkle — a base de blockchain, git e Certificate
Transparency.

**As leituras:**
- *commitment* = a raiz: um hash que compromete todo o conjunto;
- *prova de pertença* = um ramo: O(log n) hashes provam que um item está lá;
- *localizar adulteração* = descer o ramo divergente;
- *auditoria* = ler tudo.

**O resultado medido (1.048.576 itens):**
- Commitment de 1M itens: **32 bytes** (um hash) vs 33,5 MB — 1.048.576×.
- Prova de pertença: **644 bytes** (20 hashes) vs transmitir os 33,5 MB —
  52.103×. E cresce com **log n**, não com n: dobrar o conjunto adiciona
  *um* hash à prova.

**A fronteira honesta:** verificar *tudo* lê tudo (sem atalho); a árvore
custa ~2× de armazenamento; e Merkle dá *integridade*, não *sigilo*.
(Importante: criptografia de confidencialidade é o oposto deste paradigma —
um ciphertext deve parecer ruído, sem estrutura interpretável. Estrutura
explorável ali = cifra quebrada. Por isso o encaixe é integridade, não
encriptação.)

### 4.4 WAFER — múltiplas camadas no mesmo dado gravado

**A ideia:** hoje cada dado é construído pensando só em si. Mas várias
camadas *co-registradas* — RGB, profundidade, segmentação da mesma cena —
partilham a mesma estrutura espacial. Poderiam ser gravadas sobre **uma**
hierarquia, lida por lentes diferentes: a lente "RGB" dá a foto, a "IR" dá o
infravermelho, a "máscara" dá a segmentação.

**O teto, declarado antes de medir (Shannon):** N bits carregam ≤ N bits.
Não há K datasets independentes de graça. O que se partilha é a *estrutura*,
não o conteúdo.

**O resultado medido — e a humildade que ele trouxe:**
- A estrutura *é* amortizada (gravada 1× em vez de K×), mas para camadas
  pesadas em valor ela é só ~4% do custo → partilhar estrutura sozinho rende
  só **1,12×** em dado co-registrado, e **perde** (0,32×) em camadas
  desalinhadas, onde a árvore unida super-subdivide. **Partilhar estrutura
  sozinho é uma alavanca fraca.**

**Onde o ganho realmente mora** — dois levers que, juntos, flipam a foto
natural de perda para ganho:

```
união rígida ........................ 0,67× (perde)
+ luminância DERIVADA do RGB ........ 0,78×
+ REFINAMENTO local (não união) ..... 1,12× (ganha)
```

1. **Correlação entre camadas.** Shannon proíbe partilhar conteúdo
   independente — mas camadas de IA são *correlacionadas* (profundidade
   prevê-se de RGB). Gravar a camada 2..K como predição sobre a 1 partilha a
   *informação mútua*, não conteúdo novo. Derivar luminância do RGB poupou
   payload de verdade.
2. **Base + refinamento local, em vez de união rígida.** A união forçava
   todas as camadas a subdividir onde *qualquer* uma tinha detalhe (a
   segmentação arrastava a árvore RGB). A solução: uma árvore base partilhada
   + uma mini-quadtree local por camada, só onde aquela camada precisa. Isto
   fecha a fronteira do desalinhamento.

Verificado com gate de reconstrução lossless (todas as camadas voltam
exatas dos bytes contados). Escopo honesto: o 1,12× é o wafer comparado com
guardar as mesmas camadas como árvores BH independentes, na MESMA qualidade
— não contra um especialista, que em foto natural ainda venceria o próprio
BH. O wafer não derruba o JPEG; ele torna eficiente guardar a *pilha*
co-registrada que hoje se guarda replicada.

### 4.5 GPU — movimento de dados, em silício real

Este terreno fecha o laço com a motivação original do documento de Dezembro
de 2025: *"GPUs gastam 80-90% dos ciclos movendo dados."* Lá, a conclusão
foram ganhos de hardware de **5-35× inventados**. Aqui, a mesma intuição é
levada a uma **medição real**.

**A leitura:** um array grande vive na memória da GPU. Uma carga típica de
dados (agregações, passadas grosseiras, filtros) precisa, no layout
convencional, *varrer* a memória. No layout hierárquico, o agregado já está
pré-computado nos nós — responde-se lendo o resumo, não varrendo.

**Primeiro a simulação** (contagem de bytes movidos): para a carga
agregação/LOD/contexto, o layout hierárquico move **1.540× menos dados**. Mas
contar bytes não é medir tempo — então fomos ao silício.

**Depois o teste real, numa RTX 3060** (tempo de parede, CUDA events, 1 GB
em VRAM):

| tarefa | tempo flat | tempo BH | speedup real |
|---|---|---|---|
| redução total (1 GB) | 2.991 µs | 2,8 µs | **1.087×** |
| agregação de range 25% | 752 µs | 2,8 µs | **264×** |

E as três verdades que só o hardware dá — esta é a parte importante:

1. **O ganho é real e grande** (264–1.087× de tempo de parede medido).
2. **A razão de bytes exagera por ~100.000×.** A simulação dizia 128
   milhões×; o relógio deu 1.087×. A leitura hierárquica é tão pequena que
   bate no *piso de overhead de lançamento de kernel* (~2,8 µs fixos) — o
   silício tem um chão que a contagem de bytes ignorava.
3. **A premissa validou-se:** a varredura flat rodou a 342 GB/s, colada no
   teto de ~360 GB/s da placa. É genuinamente limitada por memória — logo a
   ponte "menos bytes → menos tempo" é legítima, e o ganho não é artefato.

**A fronteira honesta:** construir o agregado custa um tempo único (~15 ms);
compensa a partir de ~5 consultas que o reusem — para uma consulta só, o
convencional ganha. Vale apenas para cargas limitadas por memória. E é o BH
como *layout de software* em hardware existente — não o hardware
BH-nativo que o documento imaginou, que não existe.

**E o teste pesado, que empurrou a placa de verdade.** Para não ficar só no
teste leve, rodámos um lote de 6.000 consultas de agregação que varre
3,51 TB — a 3060 a 100% de SM por 26 s (confirmado por `nvidia-smi dmon`).
Aqui o método encontrou duas armadilhas e as corrigiu em público:
1. **o kernel flat era subótimo** — sustentou 134 GB/s (37% do teto), porque
   "um bloco por consulta" é limitado por ocupação, não por banda. O número
   bruto (4.725×) estava inflado pela má implementação do flat, não pelo BH.
2. **o lado BH estava no piso de medição** — oscilando 6–120 ms, o que faz o
   multiplicador exato tremer.
   O número que sobrevive aos dois caminhos independentes — tempo contra um
   flat *ideal* (360 GB/s) E razão de dados movidos (3,51 TB vs ~2 GB
   incluindo o build) — é **~1.750×**. Esse é o valor honesto.

A diferença entre Dezembro de 2025 e agora resume a campanha inteira: um
**prometia** 5-35× de hardware; o outro **mede** — e quando o número grande
tinha gordura (kernel ruim + ruído de piso), tirou-a e reportou o ~1.750×
que resiste. Diagnóstico completo do teste: `gpu/PROCESSO_E_DIAGNOSTICO_GPU.md`.

---

## 5. AS LEIS QUE EMERGIRAM

Os quatro terrenos, juntos, dizem a mesma coisa:

**Lei 1 — O ganho tem sempre a mesma origem.** O resumo mora nos nós (cor
média, min/max, hash); ler seletivamente toca O(log n). Thumbnail, agregação
e commitment são *a mesma leitura* em domínios diferentes.

**Lei 2 — A fronteira tem sempre a mesma forma.** Quando a interpretação não
casa com o objetivo (textura natural, valor independente da chave, auditoria
total), não há ganho. Isso não é falha do paradigma — é um *endereço vazio
na biblioteca de interpretações*. Preenchê-lo tem um custo (mais
armazenamento, ou reconstruir o estado da arte do domínio).

**Lei 3 — Uma estrutura, muitas leituras (opcionalidade sob multiplicidade).**
O valor não é vencer *uma* tarefa — um especialista sempre vence uma só. É
servir *muitas* operações de uma estrutura. Mas isto só compensa quando
(i) as operações partilham a mesma hierarquia E (ii) o ativo único é
compressivamente competitivo. Opcionalidade é necessária, não suficiente;
materializar leituras que ninguém usa é sobrecarga pura.

**Lei 4 — O ganho precisa de estrutura-dominante.** Partilhar/ler estrutura
só move a agulha quando a estrutura é fração grande do custo. Tamanho
espacial puro não faz isso (a fração estrutura/payload é invariante de
escala). É preciso *redundância* que esvazie o payload.

---

## 6. A PROVA DE ESCALA: O FILME

A Lei 4 foi testada onde ela deveria brilhar: um filme. Um filme não é uma
imagem grande — é uma imagem *com eixo de tempo*, e o tempo traz redundância
massiva (frames consecutivos são quase iguais).

Proxy de 30s (720 frames, 3 camadas co-registradas), medido:

```
independente .................. 1,00×
temporal (delta entre frames) . 1,65×
wafer (sem temporal) .......... 1,12×
wafer + temporal .............. 2,13×
```

A cadeia composta, em números: a redundância temporal **esvazia o payload**
→ a fração-estrutura sobe de **16,7% para 33,4%** → e *só então* partilhar
estrutura entre as camadas passa a valer. **O filme é onde escala E
redundância se somam.** Uma foto não tem nenhuma das duas — por isso o wafer
mede fraco nela e forte aqui.

(Ressalva: a predição temporal é o que codecs de vídeo já fazem; não é novo.
O novo é o efeito *composto* — e servir a pilha co-registrada inteira de um
filme sobre uma hierarquia espaço-temporal, com acesso progressivo, ROI e
seek no tempo, que ninguém guarda assim hoje.)

---

## 7. O QUE ISTO NÃO É (HONESTIDADE)

```
NÃO bate especialistas numa tarefa isolada
   JPEG/WebP comprimem foto natural melhor; B-tree faz lookup pontual melhor.

NÃO viola Shannon
   Múltiplas leituras não criam capacidade. São projeções e estrutura
   partilhada, nunca "K datasets de graça".

NÃO inventa os domínios
   Codecs já fazem mode-decision (AV1); bancos têm zone-maps (Parquet);
   Merkle é padrão. A contribuição é a UNIFICAÇÃO, não a engenharia.

NÃO é encriptação
   Confidencialidade exige ausência de estrutura; é o oposto da tese.
```

O valor real é nomear que decode progressivo de imagem, poda de agregação em
banco e prova de Merkle são **a mesma leitura-por-objetivo-sobre-hierarquia-
grátis** — e que a indústria convergiu para isso em campos isolados sem
perceber que era um só princípio.

---

## 8. ONDE ISTO VALE DE VERDADE (APLICAÇÕES)

Pela Lei 3 e pela Lei 4, o paradigma é a escolha certa quando o dado tem
**muitos ângulos de acesso** E **estrutura dominante (escala + redundância)**:

- **Ativos grandes acessados de muitas formas** — um filme 4K servido em
  múltiplas resoluções + seek + preview + região, de UMA estrutura, em vez
  de guardar uma escada de renditions de um arquivo enorme.
- **Pilhas co-registradas de IA** — RGB + profundidade + segmentação +
  saliência + embeddings espaciais da MESMA cena, partilhando estrutura e
  correlação. É exatamente o que modelos produzem hoje e ninguém guarda
  partilhado. (Aqui a IA não só usa o formato — ela *gera* as camadas que o
  tornam valioso.)
- **Dados científicos/geoespaciais** — bandas múltiplas co-registradas,
  consultas por agregação e região sobre a mesma grade.
- **Sistemas que precisam de integridade seletiva** — provar um item sem
  revelar o resto, sobre o mesmo dado que já serve consulta e leitura.

E *não* é a escolha certa para: um único padrão de acesso sobre conteúdo que
um especialista comprime bem (uma foto isolada num site). Ali, o especialista
vence — e usá-lo é o certo.

---

## 9. COMO REPRODUZIR

```
codec    X:\bitH\           py -m pytest tests -q   ·  src/bench/{harness,headtohead,portfolio}.py
banco    X:\bitH\db\        py -m pytest tests -q   ·  src/bench/harness.py
merkle   X:\bitH\merkle\    py -m pytest tests -q   ·  src/bench/harness.py
wafer    X:\bitH\wafer\     py -m pytest tests -q   ·  src/bench/{harness,film}.py
gpu      X:\bitH\gpu\       py -m pytest tests -q   ·  src/bench/harness.py (sim) + real_gpu.py (RTX 3060)

Python: X:/miniconda3/python.exe  (NumPy, Pillow, hashlib, CuPy/CUDA)
128 testes verdes. Correção exata é o portão antes de qualquer medição.
```

Relatórios: `RESULTS_PARADIGMA_BH.md` (síntese), `RESULTS_MVP_BH_CODEC.md`,
`RESULTS_PORTFOLIO.md`, `db/RESULTS.md`, `merkle/RESULTS.md`,
`wafer/RESULTS.md`, `wafer/RESULTS_FILME.md`, `gpu/RESULTS.md`,
`gpu/RESULTS_REAL_GPU.md`.

---

## 10. CONCLUSÃO

O documento de Dezembro de 2025 afirmava: *"o byte sempre foi uma árvore
binária implícita."* Cinco terrenos e dezenas de medições depois — o último
deles um teste real na GPU que fecha o laço com a motivação original —, a
forma forte e honesta da tese é esta:

> A árvore esteve sempre lá, em qualquer dado. O ganho não é um algoritmo
> esperto — é **escolher como ler o dado para o que se quer fazer**, e
> manter muitas leituras possíveis sobre a mesma estrutura. Esse ganho é
> real e por vezes esmagador (48× sobre o WebP no caso casado; 52.000× numa
> prova de Merkle; ∞ numa agregação) — **mas só onde há muitas leituras a
> fazer e onde a estrutura domina o custo.** Não em qualquer dado:
> exatamente onde isso vale.

A honestidade é a metade do resultado. Saber onde o paradigma *perde* —
foto natural, padrão de acesso único, conteúdo independente — é o que torna
confiável saber onde ele *ganha*. Um PoC que só mostrasse vitórias seria
propaganda. Este mostra as duas faces, medidas, e por isso a tese sobrevive.

---

*"Não é o algoritmo — é a forma de ler."*
