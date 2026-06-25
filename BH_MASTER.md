# BITS HIERÁRQUICOS — ESTUDO E DEMONSTRAÇÃO TÉCNICA
## Um envelope estrutural que orquestra representações: método, medições e fronteiras

**Autor:** Márcio M. Carvalho
**Período do estudo:** Dezembro 2025 – Junho 2026
**Hardware de referência:** NVIDIA GeForce RTX 3060 12 GB · Python 3.13 · NumPy · CuPy/CUDA · Pillow
**Cobertura de testes:** 128+ testes automatizados verdes, correção exata como portão antes de cada medição
**Natureza deste documento:** relatório técnico de demonstração — cada afirmação é acompanhada do método e do número medido
**Estado do repositório:** à frente do preprint publicado (Zenodo v1, DOI 10.5281/zenodo.20821058) — a §10 adiciona quatro protótipos usáveis (memória de agente, observabilidade, checkpoints de modelo, anotações adversas) ainda não numa versão publicada do Zenodo

---

## SUMÁRIO EXECUTIVO

Bits Hierárquicos (BH) começou como uma hipótese de Dezembro de 2025 ("o byte
é uma árvore implícita; hierarquia é interpretação"). Este estudo testou a
hipótese em **nove ângulos independentes**, com medições reais e baselines
honestos. O resultado não é "um codec melhor" — é a delimitação precisa de um
paradigma:

```
O BH NÃO comprime sinal denso melhor que JPEG/WebP/AVIF (perde — medido).
O BH É um ENVELOPE ESTRUTURAL que:
   (a) torna a estrutura explícita a custo baixo (0–6% do arquivo — medido),
   (b) roteia o resíduo de cada região ao especialista certo (orquestração),
   (c) oferece múltiplas leituras sobre a mesma estrutura (preview/ROI/prova).
```

**Resultado-âncora (medido):** um documento estruturado gravado no formato
orquestrado é **2,1× menor que o WebP E** permite ler qualquer região por
**3–55× menos bytes**, no mesmo arquivo — algo que nenhuma ferramenta SOTA
oferece junto.

**A lei transversal (medida em todos os ângulos):** o BH rende exatamente na
medida em que o dado é **estrutura** (gerado por regra, composto, hierárquico)
e não **sinal** (ruído/perceptual). No limite, o payload vira um *programa* que
gera o dado (ganhos de milhares×); a fronteira não é a entropia — é o
reconhecimento da estrutura.

**Enquadramento conceitual (adicionado após este estudo).** Uma varredura
posterior de 20 domínios (`applicability/`) reformulou o BH de *formato de
arquivo* para *propriedade de representação* — a **First-Class Interpretation
Representation (FCIR)**: interpretações rivais mantidas como entidades de 1ª
classe, co-registadas sobre um substrato imutável, sem adjudicação forçada. A
economia de substrato-partilhado que este estudo mede é real mas já é SOTA maduro
na maioria dos domínios; a nossa varredura identificou a FCIR (um nome de
trabalho) como a propriedade que melhor distingue o BH dos domínios avaliados —
um resultado, não uma verdade universal. Ver `BH_PRINCIPLE.md`.

---

## 1. METODOLOGIA (o que torna este estudo confiável)

Toda a investigação seguiu quatro regras, aplicadas sem exceção:

**1.1 Declarar antes de medir.** Cada terreno definiu alegações falsificáveis
com critério de **sucesso E de fracasso** ANTES da medição. Nenhum número foi
prometido a priori.

**1.2 Correção como portão.** Antes de qualquer comparação de desempenho, a
correção exata foi verificada (reconstrução bit-a-bit, igualdade de agregados,
prova criptográfica válida). Desempenho só se mede sobre resultado correto.

**1.3 Baseline honesto, com a distinção vs-ingênuo / vs-SOTA.** Números grandes
contra baselines ingênuos (varredura completa, transmitir tudo) são marcados
como tais e distinguidos de ganhos contra o estado da arte (WebP, HNSW, OLAP).

**1.4 Medição real, autocorreção pública.** Usou-se hardware real (RTX 3060,
CUDA events, `nvidia-smi dmon`). Quando uma medição estava enviesada a favor da
hipótese, foi corrigida em público. Três autocorreções materiais ocorreram e
estão documentadas (§7) — elas são parte da evidência de rigor.

---

## 2. A REFORMULAÇÃO DA PERGUNTA

A pergunta inicial — **"o BH é um codec melhor?"** — foi respondida, medição
após medição, com **não**. A pergunta correta só emergiu no fim da investigação:
**"o BH é um orquestrador estrutural de representações?"** — e a resposta é
**sim**. A chave foi uma separação que resolve a confusão de metade do estudo:

```
PROBLEMA DO RESÍDUO  ≠  PROBLEMA DO PARADIGMA
```

Tentar comprimir o resíduo (sinal denso) é o problema dos codecs especialistas
— e o BH perde nisso. O paradigma do BH é a estrutura, o pertencimento e as
leituras. Separadas, cada metade tem veredicto honesto e oposto.

---

## 3. OS TERRENOS TESTADOS (método + medição)

### 3.1 Codec de imagem — o BH como compressor (perde)

**Método:** codec quadtree com seleção de interpretação por nó
(LEAF/RAMP/DCT), comparado contra PNG/JPEG/WebP em frames 4K, com PSNR casado.

**Medições:**
- Conteúdo casado (gradiente, lossy): BH-rampa **2,4 KB @ 57,9 dB** vs WebP
  **116,7 KB @ 50,2 dB** → **48× menor, com qualidade maior**.
- Acesso (thumbnail de foto natural 4K): BH lê **0,148 MB** vs WebP 0,664 (4×),
  JPEG 1,0 (7×), PNG 6,5 (44×).
- Compressão de foto natural: **perde** (4–10× maior que o WebP).
- v0.3 (interpretação DCT): trocar o critério de erro de L∞ para L2 destravou o
  DCT e cortou 40–66%, mas **não fechou o gap** — falta entropy coding do resíduo.
- Imagem heterogênea (BH-compressor puro): **perde em todas as frações de foto
  (10,75× a 0% de foto)** — porque texto/UI explode a quadtree e o entropy
  coding do WebP já torna as regiões fáceis baratas.

**Conclusão do terreno:** como compressor, o BH perde. O ganho de 48× no
gradiente era um canto (conteúdo perfeitamente procedural), não a regra.

### 3.2 Banco de dados — leitura seletiva por agregação

**Método:** árvore de agregação (min/max/sum/count por nó) sobre 1.000.000 de
linhas; métrica = linhas lidas; baseline = varredura plana.

**Medições:**

| query | BH lê | plano lê | ganho | vs |
|---|---|---|---|---|
| SUM global | 0 | 1.000.000 | ∞ | ingênuo |
| SUM range 10% | 1.564 | 99.868 | 64× | ingênuo |
| COUNT chave 2% | 2.048 | 1.000.000 | 488× | ingênuo |
| COUNT valor correlacionado > p99 | 92.736 | 1.000.000 | 11× | ingênuo |
| eixo errado / valor independente / pouco seletivo | ~10⁶ | 10⁶ | 1–2× | fronteira |

**Materialização de interpretação:** filtro por região (não agregada) lia
tudo (1×); com um contador por região no nó → leitura de raiz, **0 linhas (∞)**
— ao custo de armazenamento que escala com a cardinalidade.

**Honestidade:** os ganhos são enormes vs varredura ingênua, mas o mecanismo
(resumo pré-computado) já é estado da arte (zone-maps, OLAP, materialized views).

### 3.3 Verificação / Merkle — prova seletiva

**Método:** árvore de Merkle (SHA-256, domain separation) sobre 1.048.576
itens; gate de correção cripto (prova válida verifica, forjada falha) antes de
medir; métrica = bytes/nós.

**Medições:**

| tarefa | BH lê | baseline ingênuo | ganho |
|---|---|---|---|
| commitment de 1M itens | 32 B (1 hash) | 33,5 MB | 1.048.576× |
| prova de pertença | 644 B (20 hashes) | 33,5 MB | 52.103× |
| localizar adulteração | 40 nós | 1.048.576 re-hashes | 26.214× |

A prova cresce com **log n** (1k → 10 hashes; 1M → 20). Honestidade: é a
construção padrão de Merkle (blockchain/git/CT); o estudo mostra a **unificação**
com os outros terrenos, não inventa cripto.

### 3.4 Wafer — múltiplas camadas co-registradas + escala (filme)

**Método:** quadtree-união sobre camadas co-registradas (RGB+profundidade+
segmentação); gate de reconstrução lossless por camada; medição de
estrutura-partilhada vs K árvores independentes.

**Medições:**
- União rígida: co-registrado **1,12×**; desalinhado **0,32× (perde)**;
  foto+lum+seg **0,67× (perde)**.
- Com camada derivada (luminância do RGB): **0,78×**.
- Com base + refinamento local (não-união): **1,12× (ganha)** — a foto natural
  passa de perda a ganho; verificado por reconstrução lossless.
- **Prova de escala (filme, 720 frames = 30s):** independente 1,00× · temporal
  (delta entre frames) 1,65× · wafer-still 1,12× · **wafer+temporal 2,13×**. A
  fração-estrutura sobe de **16,7% → 33,4%** com o temporal — a estrutura só
  passa a render quando a redundância esvazia o payload.

### 3.5 GPU — movimento de dados (face de leitura, em silício real)

**Método:** medição de movimento de dados (simulação) e tempo de parede real
(CUDA events, RTX 3060), com a carga visível por `nvidia-smi dmon`.

**Medições:**
- Simulação (bytes movidos, carga agregação/LOD/contexto): **1.540× menos dados**.
- Teste real leve (1 GB em VRAM): redução total flat 2.991 µs vs BH 2,8 µs →
  **1.087×**; agregação de range **264×**; banda flat **342 GB/s** (colada no
  teto de 360 → genuinamente bandwidth-bound).
- **Teste pesado (carga real):** 6.000 consultas, **3,51 TB varridos**, SM a
  100% por 26 s. Diagnóstico de duas armadilhas: (a) meu kernel flat era
  subótimo (134 GB/s = 37% do teto), inflando o número bruto (4.725×); (b) o
  lado BH no piso de medição (ruído). **Número honesto triangulado** (tempo vs
  flat-ideal E dados-movidos: 3,51 TB vs ~2 GB): **~1.750×**.

**Extrapolação (banda publicada, NÃO medida):** o ganho de lote é **invariante
de hardware** (~1.755× da 3060 à B200 — algorítmico, ambos escalam com a banda);
o ganho de consulta única **encolhe** em placas rápidas (992× → 45×), porque o
piso de lançamento de kernel é fixo.

**Modelo de hardware nativo (projeção rotulada, não medição):** com o piso a
nível de latência de memória (0,3 µs, físico) em vez de lançamento (2,8 µs,
software): latência single **9.747×**, lote **5.702×** (build near-memory),
energia **~1.755× menos** (∝ dados movidos — robusto, independe do valor pJ/B).

**Honestidade:** os números grandes são vs varredura ingênua; o mecanismo
(agregado pré-computado) é técnica padrão (OLAP/materialized views). A GPU prova
que a **face de leitura** é real e rápida em hardware; não é um produto isolado.

### 3.6 Armazenamento multimodal de IA — onde o BH foi testado fora de casa

**Método:** substrato unificado (estrutura + embeddings) vs pilha costurada
(storage + HNSW + cache + índice espacial), sobre ativo co-registrado.

**Medições (storage, fatia 1):**

| d (embedding) | unificado vs costurado |
|---|---|
| 8 | 4,0× (ganha) |
| 128 | empate |
| 256 | 0,86× (perde) |
| **768–4096 (IA real)** | **perde** |

**Autocorreção (embedding progressivo / Matryoshka):** ao tratar o embedding
como infraestrutura compressível (não payload irredutível) — prefixo no nó
interno em vez de full-d — o veredicto **move**: d=256 → 1,06×, d=1024 → 1,02×,
d=4096 → 1,00× (empata). O bulk (embedding de folha) é empate de Shannon; o
ganho fica no índice.

**Medições (acesso, fatia 2):** preview 7,6× · agregado 3,2× · ROI 2,1× ·
retrieval escopado estreito 1,4× · **retrieval largo 0,23× (perde)**.

**Decomposição de dívida arquitetural (stack RAG real):** a dívida eliminável
é **14–49%** (borderline), **dominada pela duplicação dos embeddings** (payload
denso), não pela estrutura. Conclusão: storage de IA densa não é o terreno do BH.

### 3.7 Composicional / densidade real — o sinal mais forte e seu limite

**Método (composicional):** dado simbólico — conceitos como equações de
primitivos partilhados — representado como envelope algébrico vs vetor denso.

**Medição:** **384× menor** (8 MB vs 3,07 GB para 1M conceitos), e responde
consultas estruturais ("quais conceitos usam o primitivo X?") que o vetor denso
**não consegue formular**.

**Método (densidade real):** dimensionalidade intrínseca de embeddings reais
(modelo all-MiniLM-L6-v2, 6.000 palavras PT, PCA).

**Medição:** 90% da variância em **160 de 384 dimensões** (~2,4× compressível).
**Honestidade:** isto é compressibilidade *linear* (já explorada por PCA/PQ/
Matryoshka), **não** composicionalidade simbólica. O dado real de linguagem,
na geometria do embedding, **não** é composicional-simbólico — é um subespaço
de dimensão média. O 384× vale para dado *que é* composição; o quanto do mundo
real é composicional permanece a aposta em aberto (do domínio simbólico).

### 3.8 Decode-programa — payload vira programa (a forma profunda da lei)

**Método:** o cabeçalho carrega o *programa* que gera a região (não o
resultado); o decoder executa o programa. Teste de generalidade (várias
famílias) + ruído + custo escondido.

**Medições:**

| família gerada por regra | WebP | programa | ganho |
|---|---|---|---|
| anéis | 37,8 KB | 13 B | 2.904× |
| ondas | 46,4 KB | 13 B | 3.572× |
| xadrez | 2,4 KB | 3 B | 809× |
| gradiente | 2,1 KB | 1 B | 2.096× |

**Sob ruído** (base procedural + ruído α): o programa-aware **mantém a vantagem
da estrutura** em todos os níveis de ruído (subtrai a base conhecida; o WebP-todo
paga pela estrutura que não sabe separar). **Custo escondido (declarado):** o
encoder precisa **descobrir** o programa — o problema inverso, trivial para
família conhecida, **indecidível em geral** (complexidade de Kolmogorov é
incomputável). A fronteira do BH não é a entropia do resíduo — é o
**reconhecimento da estrutura**.

### 3.9 Orquestração + união — a formulação que ganha pelo motivo certo

**Método (orquestração):** o BH roteia cada região ao especialista local
(plano→constante, gradiente→fórmula, texto→PNG, foto→WebP), comparado contra
um-codec-no-todo, em dois conteúdos.

**Medições:**

| conteúdo | WebP-todo | orquestrado | resultado |
|---|---|---|---|
| foto-pesado | 10,7 KB | 10,8 KB | 1,01× (empata) |
| **documento (formas fechadas)** | 4,8 KB | **2,2 KB** | **2,1× menor** |

Dividir em WebP por região (sem rotear paradigmas) **perde** (1,10×) — o ganho
vem do roteamento cross-paradigma, não do corte.

**Método (custo do envelope):** decomposição dos bytes do BH em framing /
estrutura explícita / resíduo. **Medição:** estrutura explícita = **0–6% do
total** (3 imagens). O cabeçalho inteligente é barato; o caro era o resíduo
(que agora se delega). *Responde a "pergunta matadora": tornar a estrutura
explícita custa muito pouco.*

**Método (a união):** documento gravado como `.bh`, medindo no mesmo arquivo as
duas faces.

**Medições:**
- Representação: **2,3 KB vs 4,8 KB do WebP = 2,1× menor**.
- Leitura seletiva: ler 1 região custa plano 87 B · gradiente 96 B · texto
  590 B · diagrama 1,8 KB — **3 a 55× menos** que o WebP, que precisa do arquivo
  todo para qualquer região.

```
WebP/AVIF → resíduo ótimo, leitura ÚNICA
PDF       → orquestra especialistas, mas lista plana, sem leitura seletiva
OLAP/GPU  → leitura seletiva, mas não é formato de representação
.bh       → as DUAS faces + hierarquia + pertencimento, num envelope só
```

---

## 4. A LEI TRANSVERSAL (medida em todos os ângulos)

```
A hierarquia rende quando a ESTRUTURA domina o custo, não o SINAL denso.
No limite: payload → PROGRAMA que gera o dado, na medida em que o dado é
gerado por regra. A fronteira não é a entropia — é o reconhecimento da estrutura.
```

| classe de dado | resultado medido |
|---|---|
| procedural / fórmula | programa minúsculo: 800–3.600× (decode-programa) |
| composicional / simbólico | envelope 384× menor + consultas que o denso não faz |
| estruturado heterogêneo | orquestração 2,1× + leitura seletiva 3–55× |
| agregável / reusado | leitura seletiva ∞–488× (banco), 1.750× (GPU) |
| co-registrado + redundante | wafer+temporal 2,13× (filme) |
| **denso / perceptual (foto, áudio, embedding)** | **perde ou empata — território do conexionismo** |

---

## 5. A TESE REORGANIZADA (apoiada na evidência)

**O BH não é um codec — é um orquestrador estrutural.** Duas faces, medidas:

- **Face de leitura** (resumo no nó → ler seletivamente é barato): GPU 1.750×,
  banco ∞/488×, Merkle 52.000×, thumbnail/ROI 4–44×. Números enormes, mas o
  mecanismo já é SOTA.
- **Face de representação** (estrutura explícita + resíduo delegado):
  orquestração 2,1× em documento. Número menor, mas **vs o estado da arte**, por
  uma propriedade arquitetural.

**A união** das duas faces num envelope (2,1× menor E navegável) é o que nenhuma
ferramenta SOTA entrega. **O valor não está no bloco comprimido — está na
estrutura que sabe o que aquele bloco significa.**

**Três escalas onde o BH sobrevive ao escrutínio:**
1. formato estrutural (um ativo) · 2. orquestrador (ativo heterogêneo) ·
3. substrato composicional (sistema simbólico). Raiz comum: estrutura > sinal.

---

## 6. FRONTEIRAS HONESTAS (para a tese não virar fé)

```
- "Ganha pelo motivo certo" ≠ "achámos o produto". É validação científica; o
  produto exige construção e adoção (engenharia, não benchmark).
- O orquestrador compete com o PDF (incumbente), não com o WebP. Seu diferencial
  — hierarquia + leituras múltiplas — é real mas não-provado como necessidade de mercado.
- Os números grandes da face de leitura são vs INGÊNUO; vs SOTA, empatam. O
  diferencial é a UNIÃO das faces, não um número isolado.
- O decode-programa exige RECONHECER a estrutura (problema inverso): trivial para
  família conhecida, indecidível em geral.
- A casa do BH é dado ESTRUTURA-DOMINANTE; em sinal denso o conexionismo reina,
  e o BH o DELEGA — não o enfrenta.
- Um formato morre sem ecossistema. O caminho não é um `.bh` genérico a competir
  com Parquet/PDF; é construí-lo nativo num domínio greenfield que já precisa dele.
```

---

## 7. AS AUTOCORREÇÕES (evidência de rigor, não de fraqueza)

Três medições foram corrigidas em público quando se mostraram enviesadas:

1. **GPU — kernel flat subótimo.** O número bruto (4.725×) inflava por má
   implementação do baseline; o número honesto triangulado é ~1.750×.
2. **Multimodal — embedding tratado como payload irredutível.** Corrigido com
   representação progressiva (Matryoshka): o storage passou de "perde" a "empata".
3. **Heterogêneo — hipótese "ganha em conteúdo misto".** Refutada pelo número
   (perde 10,75×); o ganho real exige roteamento por especialista (orquestração),
   não BH-compressor puro.

---

## 8. TRABALHO RELACIONADO (situando vs o estado da arte)

O BH não inventa as técnicas que usa — ele as **unifica**. Cada capacidade
isolada já existe e é madura; a contribuição é reuni-las num envelope
estrutural único. Situamos aqui as quatro famílias de prior art.

**Codecs adaptativos por bloco.** O JPEG (Wallace, 1991) estabeleceu o modelo
"transformada + quantização + entropy coding" com uma base global fixa (DCT).
Codecs modernos — AV1/AOMedia (Chen et al., 2018), VVC, JPEG XL — fazem
*mode decision* por bloco, escolhendo modos de predição/transformada por
região. O BH-codec compete diretamente nisto e **perde** (§3.1): falta-lhe a
maquinaria de entropy coding, e a seleção por região é o que o AV1 já faz. A
diferença do BH não é compressão — é delegar a região ao especialista (§3.9).

**Estruturas de leitura seletiva.** A leitura "ler o resumo, não os dados" é
a base de OLAP/data cubes (Gray et al., 1997), zone-maps e estatísticas por
row-group do Apache Parquet, e *materialized views*. Os ganhos de §3.2 e §3.5
(banco, GPU) são exatamente este mecanismo — enormes contra varredura ingênua,
mas **já estado da arte**. Reconhecemo-los como âncora de credibilidade, não
novidade.

**Estruturas autenticadas.** A face de verificação (§3.3) é a árvore de
Merkle (Merkle, 1987), base de Git, Certificate Transparency (Laurie, 2014)
e blockchains (Nakamoto, 2008). Não inventamos cripto; demonstramos que a
prova-de-Merkle é a *mesma* leitura-por-objetivo-sobre-hierarquia dos outros
terrenos.

**Representação compacta e dado-como-programa.** Para embeddings, a
compressibilidade que §3.6/§3.7 exploram é Product Quantization (Jégou et al.,
2011) e Matryoshka Representation Learning (Kusupati et al., 2022); a busca
vetorial é HNSW (Malkov & Yashunin, 2018). O "decode-programa" de §3.8 é a
direção da complexidade de Kolmogorov (Kolmogorov, 1965; Li & Vitányi) e tem
precedente direto no PostScript (página-como-programa, Adobe) e na geração
procedural. Formatos auto-descritivos (HDF5, Protocol Buffers, PDF/ISO 32000)
provam que "dado que carrega a própria estrutura" funciona.

**A lacuna que o BH ocupa.** Nenhum destes unifica representação + leitura
seletiva + orquestração de especialistas + hierarquia/pertencimento + provas
num único envelope. PDF orquestra mas é lista plana sem leitura seletiva; OLAP
navega mas não é formato de representação; AV1 adapta por bloco mas com uma
família de modos só. A contribuição do BH é a **união**, não os componentes.

---

## 9. REPRODUÇÃO

```
codec     X:\bitH\           py -m pytest tests -q   ·  src/bench/{harness,headtohead,portfolio,
                              heterogeneous,cost_envelope,orchestrate,union}.py
banco     X:\bitH\db\        py -m pytest tests -q   ·  src/bench/harness.py
merkle    X:\bitH\merkle\    py -m pytest tests -q   ·  src/bench/harness.py
wafer     X:\bitH\wafer\     py -m pytest tests -q   ·  src/bench/{harness,film}.py
gpu       X:\bitH\gpu\       py -m pytest tests -q   ·  src/bench/{real_gpu,heavy_gpu,extrapolate,native_model}.py
multimodal X:\bitH\multimodal\  src/{probe,fatia2,probe_progressive}.py
composic.  X:\bitH\compositional\  {probe_compositional,real_density,decode_program,program_test}.py
dívida     X:\bitH\architecture_debt\  debt_decomposition.py

Python: X:/miniconda3/python.exe  (NumPy, Pillow, hashlib, CuPy/CUDA, sentence-transformers, sklearn)
Relatórios brutos por terreno: RESULTS_*.md em cada pasta.
```

---

## 10. CONCLUSÃO

O estudo testou Bits Hierárquicos em nove ângulos independentes, com método
declarado, correção como portão, baselines honestos e autocorreção pública. O
veredicto:

> O BH não é um codec melhor — é uma forma diferente de **organizar e ler
> dados estruturados**. Onde o dado é estrutura (gerado por regra, composto,
> hierárquico, agregável, co-registrado), o ganho é real e por vezes de ordens
> de grandeza, e a sua forma mais profunda é o payload virar o *programa* que
> gera o dado. Onde o dado é sinal denso (foto, áudio, embedding), o
> conexionismo reina, e o papel do BH é **delegar** ao especialista — não
> competir. A contribuição única não é um número isolado; é a **união**, num
> envelope só, de representação enxuta, leitura seletiva, hierarquia e
> pertencimento — que nenhuma ferramenta atual oferece junta.

A prova final não é mais um benchmark; é a construção do formato num domínio
onde estrutura e pertencimento importam tanto quanto o tamanho.

### Da tese aos artefatos — quatro protótipos usáveis

A construção já não é um passo, mas quatro, e todos partilham **um envelope** —
prova de que o paradigma generaliza entre domínios. Cada um é uma biblioteca
Python com demo medida e testes; cada um lê só a fração que a consulta pede, em
bytes reais lidos do arquivo.

**`bhmem` — memória de agente.** O agente grava memórias estruturadas
(fato/evento/relação + tempo + tópico + proveniência); o formato as expõe pelas
múltiplas leituras.

| leitura | o que devolve | bytes lidos | vs store plano (lê tudo) |
|---|---|---|---|
| `summary()` | resumo de todos os tópicos | 2,5% | **35× menos** |
| `recall(tópico)` | as memórias de um ramo | 4,0% | **22× menos** |
| `since(t)` | memórias da janela temporal | 9,8% | **9× menos** |
| `provenance(id)` | fonte+caminho de 1 memória | 10,8% | **8× menos** |

*(Demo: ~90 dias, 60 tópicos, 2 250 memórias; 9/9 testes verdes.)*

**`bhtrace` — traces distribuídos (observabilidade).** Um trace é uma árvore
(trace → spans → eventos); a estrutura é o índice, os atributos pesados (SQL,
stack traces, headers) são o resíduo.

| leitura | o que devolve | vs store plano |
|---|---|---|
| `summary()` / `critical_path()` | o esqueleto sem o payload | **9× menos** |
| `subtree(span)` | um drill-in | **9× menos** |
| `service(name)` | um serviço | **5× menos** |

*(Demo: trace de checkout com 269 spans, pesado em atributos; 9/9 testes verdes.)*

**`bhckpt` — checkpoints de modelo.** Um checkpoint é uma hierarquia
(modelo → camadas → tensores → experts); os pesos dominam, a estrutura é minúscula.

| leitura | o que devolve | vs checkpoint plano |
|---|---|---|
| `summary()` | arquitetura de um modelo de 16 MB lida em 9 KB, sem pesos | **1 779× menos** |
| `expert(i, e)` | carregar um expert MoE sem a mistura | **20× menos** |
| `layer(i)` / `tensor(name)` | uma camada / um tensor | **12× / 10× menos** |

*(Demo: transformer de 4 camadas, 2 camadas MoE × 6 experts, 16,2 MB; 8/8 testes verdes.)*

**`bhanno` — anotações adversas (a matriz de interpretações adversas).** A forma
mais forte das "múltiplas leituras": o mesmo substrato gravado **uma vez**, com K
anotadores a colocar camadas co-registadas que **discordam**. O wafer (§3.4)
generalizado de camadas aditivas para camadas rivais.

| leitura | o que devolve | resultado |
|---|---|---|
| armazenamento | K interpretações rivais vs K cópias independentes | **4,6× menor** (5 anotadores) |
| `adjudicate()` | maioria + concordância, lendo só os labels (sem substrato) | **11× menos** que o full |
| `item_views(id)` | todas as K interpretações de um item (a matriz) | **23× menos** |

*(Demo: 200 itens, substrato de 6 KB cada, 5 anotadores; 62% de concordância, 75 contestados; 9/9 testes verdes.)*

**Fronteira honesta, a mesma nos quatro:** o BH ganha no acesso estrutural e
**delega** o resíduo denso (busca full-text → índice invertido; quantização
por-tensor → o seu especialista; recall semântico denso → um índice vetorial).
No `bhckpt`, a leitura seletiva por-tensor já existe (`safetensors`) — essa é a
*âncora*; o novo é a *união* (hierarquia incluindo o expert MoE como leitura de
1ª classe, roteamento por-tensor, uma face Merkle para proveniência). No
`bhanno`, o envelope *expõe* o conflito; não decide quem tem razão.

Isto não são mais ângulos medidos — é a tese virando ferramentas, o **mesmo
envelope provado em quatro domínios**. O ganho escala com o quanto o dado é
estrutura-dominante — a lei transversal da §4. Ver os READMEs (`bhmem/`,
`bhtrace/`, `bhckpt/`, `bhanno/`).

---

*"O valor não está no bloco comprimido. Está na estrutura que sabe o que aquele
bloco significa."*
