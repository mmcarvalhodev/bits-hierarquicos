# BH CODEC — SPEC DO MVP
## Prova de conceito: codec de imagem com Bits Hierárquicos

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Origem:** `arquitetura_bits_hierarquicos.md` (Dezembro 2025)
**Status:** SPEC — aguardando implementação

---

## 1. TESE E ALEGAÇÕES FALSIFICÁVEIS

Tese-mãe do documento original: *hierarquia é uma questão de interpretação
da informação — o dado já é uma árvore; o BH explicita e cobra o dividendo.*

O MVP traduz a tese em três alegações mensuráveis. Cada uma tem critério
de sucesso E de fracasso. Nenhum número é prometido antes da medição.

```
C1 — DECODE PROGRESSIVO É ESTRUTURAL
     O custo de leitura escala com a resolução PEDIDA, não com a armazenada.
     Medida: bytes lidos ÷ bytes totais, por resolução alvo.
     Expectativa geométrica (a confirmar): thumbnail ~1-2%, 480p ~5-10%,
     1080p ~25-35%, 4K = 100%.
     Fracasso: se a fração medida ficar sistematicamente >2× a geométrica.

C2 — ROI É PROPORCIONAL À REGIÃO
     Decodificar uma região custa O(área da região) em payload + O(estrutura).
     Medida: bytes de payload lidos vs fração de área pedida.
     Fracasso: se o custo não escalar linearmente com a área.

C3 — COMPRESSÃO É ACEITÁVEL (não vencedora)
     O preço pago pelas propriedades C1/C2 é limitado.
     Medida: tamanho BH vs PNG (lossless) e vs JPEG (lossy, a PSNR igual).
     Sucesso: ≤2× PNG em foto natural; ≤PNG em conteúdo sintético.
     Fracasso: >2× PNG em natural — formato sangra demais.
```

**Resultado negativo é resultado.** Se C1-C3 falharem, o relatório final
documenta onde e por quê — isso encerra a especulação com dados.

## 2. NÃO-OBJETIVOS (fronteira anti-especulação)

```
NÃO é vídeo            — sem motion compensation, sem inter-frame. Fase 2 se MVP passar.
NÃO compete com AV1    — décadas de entropy coding e psicovisual. Baseline é PNG/JPEG.
NÃO mede wall-clock vs C — Python vs libpng é injusto. Medimos trabalho algorítmico
                          (bytes lidos, nós visitados). Wall-clock só BH-vs-BH.
NÃO promete ganhos de hardware — nada de NPU/ASIC/ciclos. Isso fica fora até
                          existir medição em software.
```

## 3. FORMATO DE ARQUIVO `.bhc` (v0)

### 3.1 Estrutura geral

```
[MAGIC "BHC0" 4B]
[GLOBAL HEADER]
[LEVEL TABLE]
[LEVEL 0] [LEVEL 1] ... [LEVEL N]
```

O stream é ordenado por nível (BFS). Decode progressivo = ler até o nível
desejado e PARAR. Esta ordenação é a materialização da tese: o mesmo
arquivo é todas as resoluções; a resolução é quanto dele foi lido.

### 3.2 GLOBAL HEADER

| Campo | Tamanho | Conteúdo |
|---|---|---|
| width, height | 2×4B | dimensões originais |
| levels | 1B | profundidade da árvore (níveis 0..N) |
| mode | 1B | bit0: lossless/lossy; bit1: pirâmide de médias presente |
| colorspace | 1B | 0=GRAY, 1=RGB (v0: RGB) |
| threshold | 4B float | limiar de homogeneidade (lossy; 0.0 = lossless) |

### 3.3 LEVEL TABLE

Para cada nível: offset absoluto + tamanho da seção de estrutura + tamanho
da seção de dados. Permite seek directo a qualquer nível (base do ROI).

### 3.4 Cada nível = estrutura separada de payload

```
[LEVEL k] = [STRUCTURE SECTION][DATA SECTION]

STRUCTURE: 1 byte por nó interno do nível k-1 → tipos dos 4 filhos
           (2 bits cada: 00=LEAF, 01=INTERNAL, 10=VAZIO/fora da imagem)
DATA:      payloads em ordem de varredura:
           - folhas: cor (3B RGB)
           - nós internos: cor média (3B RGB) SE pirâmide habilitada
```

Racional da separação: a estrutura é minúscula (1B/nó interno) e o payload
é o volume. O decoder ROI lê TODA a estrutura dos níveis no caminho (barato)
e faz seek só nos payloads da região (caro). Isto preserva C2 sem índices
auxiliares complexos no v0.

Correspondência com o formato `[HEADER | HIERARCHY | DATA]` do documento
original: o HEADER vira os 2 bits de tipo por filho; o campo HIERARCHY
(nível + posição) fica **implícito na ordenação BFS** — a posição é
derivável, não armazenada. Esta é uma descoberta de design que o MVP já
entrega: armazenar hierarquia explícita por nó (24 bits no doc original)
seria overhead puro quando a ordenação do stream já a codifica. A
hierarquia é, literalmente, interpretação da posição no stream.

### 3.5 Pirâmide de médias (o preço do progressivo)

Para um preview válido no nível k, ramos ainda não resolvidos precisam de
uma cor. Solução: cada nó interno armazena a média do seu quadrante.

Custo teórico: soma geométrica 1/4 + 1/16 + ... → **~33% de payload extra**
sobre as folhas. Este é o preço de entrada pago pelas propriedades de
saída. É MEDIDO e reportado (modo com/sem pirâmide), nunca escondido.

## 4. ENCODER

```
1. Pad da imagem para quadrado potência de 2 (registrar dims reais no header)
2. Decomposição quadtree top-down:
   - quadrante homogéneo (lossless: pixels idênticos; lossy: desvio ≤ threshold)
     → LEAF com cor (média, se lossy)
   - heterogéneo → INTERNAL, recursão nos 4 filhos
   - pixel único → LEAF
3. Serialização BFS: nível a nível, estrutura + payload
```

Lossy v0 = threshold de variância por quadrante. Sem DCT, sem quantização
perceptual — é o lossy mais simples que permite a curva tamanho×PSNR.

## 5. DECODERS (os três modos de leitura — onde mora a prova)

| Decoder | Lê | Prova |
|---|---|---|
| `decode_full` | arquivo inteiro | correctness (lossless: bit-exact com original) |
| `decode_progressive(max_level)` | header + níveis 0..k, **para** | C1 |
| `decode_roi(x, y, w, h)` | estrutura de todos os níveis + payload só dos nós que intersectam a região | C2 |

Cada decoder reporta: bytes lidos, nós visitados, seeks realizados.
A instrumentação é parte do formato do resultado, não acessório.

## 6. CORPUS DE TESTE

3 classes × ≥3 imagens, todas ≥4K (3840×2160):

```
SINTÉTICO   — cor chapada, gradientes, formas geométricas (gerados em código)
SCREENSHOT  — UI/texto/diagramas (o caso de uso forte da quadtree)
NATURAL     — fotografia real (folhagem, pele, ruído — o caso adversarial)
```

O corpus natural é onde C3 deve apanhar. Incluí-lo é obrigatório:
benchmark só com sintético seria a especulação de volta por outra porta.

## 7. MÉTRICAS E RELATÓRIO FINAL

Por imagem × modo (lossless / lossy em 3 thresholds):

```
1. Tamanho: BH vs BMP(raw) vs PNG vs JPEG (a PSNR comparável)
2. Curva C1: bytes lidos × resolução alvo (thumb/480p/720p/1080p/4K)
3. Curva C2: bytes lidos × fração de área ROI (1%, 5%, 25%, 50%)
4. PSNR (modos lossy)
5. Overhead da pirâmide: tamanho com vs sem médias
6. Contadores: nós totais, profundidade efetiva, folhas por nível
```

Entregável: `RESULTS.md` com tabelas + os dois gráficos-chave (curvas C1 e
C2 por classe de conteúdo). Veredicto explícito por alegação:
CONFIRMADA / PARCIAL / REFUTADA, com os números ao lado.

## 8. ESTRUTURA DO PROJETO

```
X:\bitH\
├── arquitetura_bits_hierarquicos.md   # documento conceitual original
├── BH_CODEC_MVP_SPEC.md               # esta spec
├── src/
│   ├── bhc/
│   │   ├── format.py        # constantes, header, level table
│   │   ├── encoder.py       # quadtree + serialização BFS
│   │   ├── decoder.py       # full / progressive / roi + instrumentação
│   │   └── metrics.py       # PSNR, contadores
│   └── bench/
│       ├── corpus.py        # geração sintética + carga do corpus
│       └── harness.py       # roda matriz imagem×modo, emite RESULTS.md
├── data/corpus/             # imagens de teste (não versionadas se pesadas)
├── tests/
│   ├── test_roundtrip.py    # lossless bit-exact, dims ímpares, 1px, etc.
│   ├── test_progressive.py  # C1: preview válido + bytes lidos corretos
│   └── test_roi.py          # C2: região correta + proporcionalidade
└── RESULTS.md               # gerado pelo harness — o veredicto
```

Stack: Python 3.13, NumPy, Pillow (I/O e baselines PNG/JPEG), pytest.
Standalone — não importa nada do intent-ai. (A ponte BH↔CS do doc
original, seção 12, é campanha separada se o MVP passar.)

## 9. FASES

```
F1 — Formato + encoder + decode_full. Gate: roundtrip lossless bit-exact
     no corpus inteiro.
F2 — decode_progressive + decode_roi + instrumentação. Gate: testes C1/C2
     verdes (preview válido, bytes contados, ROI exacto).
F3 — Modo lossy (threshold) + PSNR. Gate: curva tamanho×PSNR monotónica.
F4 — Harness completo + RESULTS.md. Gate: veredicto por alegação com
     números reais. Decisão: fase vídeo / ajustar formato / encerrar.
```

## 10. RISCOS CONHECIDOS (declarados antes de medir)

```
R1 — Foto natural degenera a árvore em folhas-por-pixel → C3 falha no
     lossless. Mitigação possível (fase posterior): delta encoding entre
     irmãos, ou entropy coding leve (zlib no payload) — se usado, reportar
     separado para não contaminar a medição do formato puro.
R2 — Pirâmide de médias (~33%) pode empurrar C3 acima do limite 2×PNG.
     Por isso o modo sem pirâmide existe: separa o custo do formato do
     custo da propriedade progressiva.
R3 — Artefactos de bloco no lossy são esperados e aceites no v0 — o MVP
     prova propriedades de acesso, não qualidade perceptual.
```

---

*O ganho do BH não é fazer o mesmo trabalho mais rápido — é tornar nativas
operações de leitura que formatos flat não têm. O custo disso é pago na
escrita e está na conta. Esta spec existe para que a conta seja real.*
