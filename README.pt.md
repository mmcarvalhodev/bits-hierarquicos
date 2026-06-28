[English](README.md) · **Português**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20821058.svg)](https://doi.org/10.5281/zenodo.20821058)

# Bits Hierárquicos (BH)

> **Bits Hierárquicos (BH) é um modelo de representação onde múltiplas
> interpretações — possivelmente contraditórias — partilham um substrato imutável
> e permanecem consultáveis, sem duplicar o dado nem as forçar a uma única
> verdade.**

📄 **Leia online (site bilíngue):** https://mmcarvalhodev.github.io/hierarchical-bits/

O coração, numa linha: **não duplicar o mundo toda vez que alguém discorda dele.**
Parte de uma base comum — um dataset, um edifício, um conjunto documental, um
histórico. Sobre ela surgem várias interpretações: anotadores rotulam-na,
disciplinas leem-na de forma diferente, hipóteses competem, versões acumulam-se.
Hoje, segurá-las obriga a uma escolha má — **copiar a base** uma vez por
interpretação, ou **fundir numa só** e perder o resto.

![FCIR — o modelo numa imagem: interpretações rivais co-registadas sobre um substrato imutável, com adjudicação opcional no momento da leitura](pitch_assets/fcir_diagram.svg)

O mesmo modelo, em texto (para leitores — humanos ou máquinas — que não renderizam SVG):

```
   Interp A (alice):  céu   gato  rua     ┐
   Interp B (bob):    céu   gato  rua     ├ coexistem · co-registadas · 1ª classe
   Interp C (carol):  céu   CÃO   rua     ┘ (discordam em e₂ — ambas mantidas)
                       │     │     │
   substrato:          e₁    e₂    e₃       imutável · guardado uma vez
                             │
       adjudicação no momento da leitura (OPCIONAL · não armazenada):
          σ uma lente   ·   maioria → "gato"   ·   ⊥ manter a discordância
```

## O que o torna diferente — e o que não torna

Guardar um substrato uma vez e ler seletivo **já é SOTA maduro** — DICOM,
COG/STAC, lakeFS, CRAM/tabix, S-LoRA, MAM. O BH **não** reivindica inventar isso.
Uma [varredura de 20 domínios](applicability/) apontou a propriedade ainda pouco
explorada, à qual damos um **nome de trabalho**: a **First-Class Interpretation
Representation (FCIR)** — interpretações mantidas como entidades persistentes,
endereçáveis e co-iguais sobre um substrato partilhado, com adjudicação
**diferida e opcional**.

> A afirmação honesta, com o escopo do que varremos: **a nossa investigação
> identificou a FCIR como a propriedade que melhor distingue o BH das abordagens
> avaliadas** — um resultado, não uma lei universal, e um nome de trabalho que
> deve seguir a ideia, não aprisioná-la. Ver [`BH_PRINCIPLE.md`](BH_PRINCIPLE.md).

**O teste distintivo (falsificável):** dadas duas interpretações que discordam
sobre o mesmo elemento, podem **ambas permanecer** — nenhuma marcada como errada
— até alguém escolher (ou recusar) adjudicar? Muitos sistemas convergem para uma
verdade, ou isolam cada leitura numa cópia/versão independente. O BH mantém-nas
co-registadas sobre um substrato e deixa a adjudicação esperar.

## Prior art — honestamente

Um teste cego teve cinco revisores independentes a apontar imediatamente sistemas
que já fazem partes disto. Tinham razão, e **dois já o fazem por inteiro**, cada
um no seu domínio: **RDF named graphs + proveniência** (para triplos) e
**standoff annotation** (W3C Web Annotation, UIMA — para texto/média; o nosso
protótipo `bhanno` *é* standoff annotation, não a inventou). Git branches, bancos
bitemporais / Datomic, CRDTs e event sourcing fazem cada um algo *adjacente mas
distinto* (merge eventual, supersessão temporal, auto-convergência, vistas
derivadas).

Portanto **a FCIR não é um mecanismo novo** — é uma **síntese arquitetural e um
nome**: um termo + um teste falsificável para uma propriedade que hoje existe só
domínio-a-domínio, sem vocabulário partilhado entre triplos, anotação, BIM, pesos
de modelo e memória de agente. **Julga-a como síntese, não como invenção.** A
confrontação completa — incluindo onde os sistemas existentes ganham — está em
[`BH_PRINCIPLE.md`](BH_PRINCIPLE.md#how-fcir-relates-to-adjacent-systems).

## O que há neste repositório

| | |
|---|---|
| [`BH_PRINCIPLE.md`](BH_PRINCIPLE.md) | **O conceito** — FCIR (nome de trabalho), o teste falsificável, e a confrontação honesta com sistemas adjacentes. |
| [`BH_ALGEBRA.md`](BH_ALGEBRA.md) | **O modelo formal** — operadores + leis; FCIR como `⊕ ⊥ α` (coexistência desacoplada da adjudicação). |
| [`CONCLUSION.md`](CONCLUSION.md) | **Conclusão provisória** — a hipótese de paradigma universal não foi confirmada; o que sobreviveu; resposta à crítica externa. |
| [`applicability/`](applicability/) | A varredura de 20 domínios, pontuada e ranqueada (maioria ANCHOR; um BUILD). |
| [`DIRECTIONS_EVAL.md`](DIRECTIONS_EVAL.md) | **Fronteiras exploradas (becos sem saída validados)** — 3 direções propostas, testadas e descartadas; registo honesto do limite de abrangência. |
| [`BH_MASTER.md`](BH_MASTER.md) | O estudo medido: 9 ângulos testados, método declarado, baselines honestos, autocorreções públicas, Related Work. |
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

*"Não duplicar o mundo toda vez que alguém discorda dele."*
