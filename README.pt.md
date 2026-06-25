[English](README.md) · **Português**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20821058.svg)](https://doi.org/10.5281/zenodo.20821058)

# Bits Hierárquicos (BH)

> **Um envelope estrutural: representa um ativo heterogêneo, navega por partes
> dele sem carregar tudo, e delega cada região ao melhor formato especialista.**

📄 **Leia online (site bilíngue):** https://mmcarvalhodev.github.io/hierarchical-bits/

A maioria dos formatos te obriga a escolher **um**: *compacto* (JPEG/WebP — mas
para ver um pedaço, decodifica tudo) **ou** *navegável* (índices, OLAP, vector
DB — mas é estrutura colada por cima, em vários sistemas que precisam ser
sincronizados). O BH grava **um envelope** onde a estrutura é parte do formato:
compacto **e** navegável, num arquivo só.

```
1. torna a estrutura EXPLÍCITA   — hierarquia, pertencimento (custo: 0–6%)
2. ROTEIA cada região            — foto→WebP, gradiente→fórmula, texto→PNG
3. permite MÚLTIPLAS leituras    — preview / região / agregado / prova
```

## A capacidade central (não um benchmark)

O coração do BH não é "ser menor". É **ler só a parte que você precisa, sem
decodificar o resto** — uma propriedade do formato, não de um dataset.

**`bhmem`** ([`bhmem/`](bhmem/)) é o primeiro artefato usável: memória de agente
como `.bh`. O agente lê o resumo, um tópico, uma janela temporal ou a
proveniência **sem carregar a memória inteira** (medido em bytes reais lidos):

| leitura | bytes lidos | vs store plano (lê tudo) |
|---|---|---|
| `summary()` — resumo de todos os tópicos | 2,5% | **35× menos** |
| `recall(tópico)` — um ramo | 4,0% | **22× menos** |
| `since(t)` — janela temporal | 9,8% | **9× menos** |
| `provenance(id)` — fonte de 1 memória | 10,8% | **8× menos** |

## Onde rende e onde delega (a fronteira honesta)

```
GANHA   dado ESTRUTURA-dominante: documentos, diagramas, dados em camadas,
        saídas estruturadas de IA, conhecimento simbólico. No limite (dado
        gerado por regra): o payload vira o PROGRAMA que o gera — 800–3.600×.
DELEGA  sinal denso (foto, áudio, embedding) → WebP/AVIF/HNSW reinam, e o BH
        os CONVOCA. Não compete onde não deve.
```

A fronteira não é a entropia — é o **reconhecimento da estrutura**.

## O que há neste repositório

| | |
|---|---|
| [`BH_MASTER.md`](BH_MASTER.md) | O estudo sério: 9 ângulos testados, método declarado, baselines honestos, autocorreções públicas, Related Work. |
| [`BH_PITCH_APRESENTACAO.md`](BH_PITCH_APRESENTACAO.md) | Pitch de apresentação (7 slides). |
| [`BH_PITCH_VISUAL.md`](BH_PITCH_VISUAL.md) + [`pitch_assets/`](pitch_assets/) | Pitch com 4 gráficos comparativos. |
| [`bhmem/`](bhmem/) | **Protótipo usável** — memória de agente em `.bh` (lib + testes, 35×/22×/9×/8×). |
| [`bhtrace/`](bhtrace/) | **Protótipo usável** — um trace distribuído em `.bh` (ler o esqueleto sem o payload, ~9× menos). |
| [`bhckpt/`](bhckpt/) | **Protótipo usável** — um checkpoint de modelo em `.bh` (arquitetura sem os pesos ~1.800× menos; carregar um expert MoE ~20× menos). |
| [`bhanno/`](bhanno/) | **Protótipo usável** — anotações adversas (K rotulagens rivais sobre um substrato, ~4.6× vs K cópias; adjudicação lê só os labels). |
| `db/` `merkle/` `wafer/` `gpu/` `compositional/` … | Os terrenos testados, cada um com código + `RESULTS_*.md`. |

*Versões em inglês: `BH_MASTER.en.md`, `BH_PITCH_APRESENTACAO.en.md`,
`BH_PITCH_VISUAL.en.md`. O site (`build_site.py`) gera ambos os idiomas.*

## Reproduzir

```bash
python bhmem/demo.py                      # demo medida + testes
python -m pytest bhmem/tests/ -q
python pitch_assets/generate_charts.py    # gráficos PT + EN
python pitch_assets/generate_evidence.py
python build_site.py                      # site bilíngue (EN padrão + PT)
```

## Licenças (dupla)

- **Código** (`*.py`, testes, benchmarks) → **Apache License 2.0** — ver
  [`LICENSE`](LICENSE). Permissiva, com cláusula de patente explícita.
- **Documentos** (`*.md` de estudo, relatório, pitch) → **CC BY 4.0** — ver
  [`LICENSE-docs.md`](LICENSE-docs.md). Cite, traduza, redistribua, inclusive
  comercialmente, mantendo a atribuição.

## Autor & citação

**Márcio M. Carvalho** (2025–2026).

> Carvalho, Márcio M. *Bits Hierárquicos — Estudo de um envelope estrutural.*
> 2025–2026. Licença de documentação: CC BY 4.0.

---

*"O valor não está no bloco comprimido. Está na estrutura que sabe o que aquele
bloco significa."*
