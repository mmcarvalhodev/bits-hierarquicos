# BH Codec v0.3 - Alteracoes Implementadas

## Objetivo

Esta rodada nao trata o codec como fim. O codec continua sendo o teste da tese BH:
mudar a forma de representar e ler dados permite que cada regiao escolha a
interpretacao que melhor explica seu conteudo.

O problema observado em `RESULTS.md` era claro: a v0.2 tinha poucas
interpretacoes por no. Ela funcionava muito bem quando o conteudo casava com
`LEAF` ou `RAMP`, mas perdia para codecs polidos em foto natural e textura.

## O que mudou

### 1. Biblioteca de interpretacoes expandida

Foi adicionado um novo tipo de no terminal:

```text
DCT = 4
```

Esse no representa o quadrante por uma mini-DCT com os coeficientes de baixa
frequencia:

```text
4 x 4 coeficientes x 3 canais x int16 = 96 bytes por no DCT
```

Arquivo novo:

```text
src/bhc/dct.py
```

Ele implementa:

```text
encode_blocks()
reconstruct()
```

O encoder e o decoder usam a mesma reconstrucao, preservando a regra do MVP:
se o encoder aceitou o erro, o decoder reproduz a mesma interpretacao.

### 2. Formato preparado para mais de 4 tipos

A v0.2 usava 2 bits por filho na estrutura. Isso era compacto, mas prendia o
paradigma a apenas 4 codigos:

```text
LEAF, INTERNAL, EMPTY, RAMP
```

Na v0.3 foi adicionado o flag:

```text
MODE_WIDE_TYPES = 0x04
```

Quando esse flag esta ativo, a estrutura grava 1 byte por filho. Isso permite
adicionar novos tipos como `DCT` e futuras interpretacoes (`PALETTE`, `MASK`,
`DCT8`, `EDGE`, etc.).

Importante: o modo compacto continua existindo. O encoder usa estrutura larga
apenas em modo lossy, onde a nova biblioteca de interpretacoes entra.

### 3. Encoder agora tenta frequencia antes de subdividir

O fluxo conceitual de decisao por no passou a ser:

```text
1. Se o bloco e homogeneo dentro do threshold -> LEAF
2. Senao, se rampa bilinear explica o bloco -> RAMP
3. Senao, em lossy, se mini-DCT explica o bloco -> DCT
4. Senao -> INTERNAL
```

Depois da primeira medicao, essa regra foi refinada: `DCT` nao e mais aceito
apenas porque cabe no erro. O encoder primeiro monta a arvore compacta
`LEAF/RAMP/INTERNAL`, calcula custo acumulado bottom-up por no, e so troca
uma subarvore por `DCT` quando:

```text
custo_da_subarvore > payload_DCT
```

Depois disso, ha uma trava global:

```text
arquivo_com_DCT_e_wide_types < arquivo_compacto_sem_DCT
```

Se essa conta nao fechar, o encoder volta automaticamente para a arvore
compacta v0.2. Isso evita que uma interpretacao nova piore o arquivo por
causa do custo estrutural de permitir mais tipos.

### 4. Decoders atualizados

Foram atualizados:

```text
decode_full
decode_progressive
decode_roi
decode_structure_map
```

`DCT` e tratado como no terminal, igual a `LEAF` e `RAMP`: se a regiao
intersecta o bloco, o payload DCT e lido e reconstruido naquele quadrante.

### 5. Instrumentacao

O `stats` retornado por `encode()` agora inclui:

```text
wide_types
total_dct
per_level[].dct
```

Isso permite medir quando a nova interpretacao esta sendo usada.

## Testes adicionados

Arquivo novo:

```text
tests/test_dct.py
```

Coberturas adicionadas:

```text
1. natural_proxy usa nos DCT em modo lossy
2. ROI com blocos DCT bate com decode_full
3. decode_progressive no nivel completo bate com decode_full
```

Resultado da suite:

```text
60 passed
```

Houve apenas um warning do pytest por falta de permissao para atualizar
`.pytest_cache`; nao afeta os testes.

## Medicao rapida

Com `natural_proxy(512, 512)`, `threshold=24`, `pyramid=False`:

```text
tamanho: 96,680 bytes
total_dct: 992
total_ramps: 2
PSNR: 36.64 dB
```

Com `gradient(512, 512)`, `threshold=4`, `pyramid=False`:

```text
tamanho: 112 bytes
total_dct: 0
total_ramps: 1
PSNR: 58.63 dB
```

Isso mostra a selecao correta dentro da biblioteca:

```text
gradiente -> RAMP
conteudo natural suave -> DCT
```

Depois do seletor bottom-up e da trava global, a medicao pontual em 4K com
`threshold=24` ficou:

```text
natural_city     1.604 MB, PSNR 32.85, DCT=0, wide_types=False
natural_forest   0.245 MB, PSNR 32.62, DCT=0, wide_types=False
natural_portrait 0.241 MB, PSNR 32.96, DCT=0, wide_types=False
```

Ou seja: para essas fotos reais, o DCT atual ainda nao paga o custo de abrir
o formato para tipos largos. A melhoria real aqui e de engenharia do seletor:
a nova interpretacao existe, mas nao entra quando piora o resultado.

## Arquivos alterados

```text
src/bhc/format.py
src/bhc/encoder.py
src/bhc/decoder.py
src/bhc/structure_map.py
src/bhc/dct.py
tests/test_dct.py
BH_CODEC_V0_3_CHANGES.md
```

## O que ainda falta para virar o jogo contra codecs polidos

Esta v0.3 implementa a primeira peca importante: uma interpretacao de
frequencia e um seletor que evita regressao. Para realmente disputar com
JPEG/WebP em foto natural, ainda faltam tres passos:

```text
1. Rate-distortion real
   Escolher LEAF/RAMP/DCT/INTERNAL por custo = bytes + lambda * erro.

2. Entropy coding por tipo de payload
   DCT sem zig-zag/RLE/Huffman/ANS ainda grava coeficiente cru.

3. Mais interpretacoes para UI/screenshot
   PALETTE, MASK2COLOR, EDGE e RUNS devem atacar o caso em que PNG ainda
   vence por explorar repeticao e poucas cores melhor que a v0.3.
```

## Leitura BH da mudanca

A melhoria nao veio de "otimizar o codec". Veio de aumentar a biblioteca de
formas de leitura.

Na v0.2, o dado podia ser lido como constante ou rampa. Na v0.3, uma regiao
tambem pode ser lida como frequencia local. Isso e exatamente a tese BH em
acao: a estrutura continua hierarquica, mas o ganho aparece quando a
interpretacao certa existe e pode ser selecionada por regiao.
