# bhmem — memória de agente como envelope `.bh`

> Protótipo mínimo **usável** da tese dos Bits Hierárquicos, aplicada a um
> domínio concreto: a memória de um agente.

A memória de um agente hoje é espalhada por sistemas separados — documentos,
embeddings, resumos, cache, índices, metadados — que precisam ser
sincronizados. O `bhmem` grava **um envelope hierárquico** onde a *estrutura é
parte do formato*. O agente não carrega a memória inteira para usar um pedaço:

```python
from bhmem import Memory, MemoryStore, MemoryReader

store = MemoryStore()
store.add(Memory(id="m1", ts=1_700_000_000.0, kind="fact",
                 topic="projeto_auth", text="OAuth com PKCE, tokens de 15 min.",
                 source="turno#42 · ferramenta:read"))
store.save("agent_memory.bh")

mem = MemoryReader("agent_memory.bh")

mem.summary()                 # resumo de TODOS os tópicos — lê só o índice
mem.recall("projeto_auth")    # as memórias de UM tópico — lê só esse ramo
mem.since(1_700_500_000.0)    # memórias recentes — pula ramos fora da janela
mem.provenance("m1")          # fonte+caminho de 1 memória — lê só o bloco dela
mem.full()                    # tudo — a linha de base
```

Cada leitura devolve `(resultado, stats)` onde `stats` reporta os **bytes que
realmente leu** do arquivo (seeks reais) — para o ganho ser medido, não alegado.

## O valor: ler só o que precisa

Demo realista (agente rodando ~90 dias: 60 tópicos, 2 250 memórias):

| leitura | % do arquivo lido | vs store plano (lê tudo) |
|---|---|---|
| `summary()` | 2,5% | **36× menos bytes** |
| `recall(tópico)` | 4,0% | **22× menos bytes** |
| `since(últ. 5 dias)` | 9,8% | **9× menos bytes** |
| `provenance(id)` | 10,8% | **8× menos bytes** |
| `full()` | 100% | 1× (linha de base) |

A linha de base honesta é um store plano (JSONL): para **qualquer** consulta
ele carrega o arquivo inteiro, porque não tem estrutura para navegar. O `.bh`
salta para o ramo pedido. O ganho **escala com o número de ramos** e com o
enviesamento do acesso — é a mesma lei do estudo: a leitura seletiva rende
quando há muitos ramos e o índice não afoga o payload.

## O formato `.bh`

```
MAGIC(4)
header_len(4)  + header_json     {n_topics, n_mem}
table_len(4)   + table_json      resumos por tópico + offset/size  (índice de estrutura)
idindex_len(4) + idindex_json    {id -> tópico}   (só provenance carrega)
bloco_tópico_0 ... bloco_tópico_n   memórias por ramo
```

A **posição** codifica a hierarquia (não há campo "hierarquia"). O índice de
estrutura é pequeno e lido sempre; os blocos ficam no fim e são lidos por seek,
só quando a consulta os pede. O `id_index` é uma região separada para que o
resumo não pague pelo mapa de ids.

## Fronteira honesta (a mesma do estudo)

- **Ganha** em acesso *estrutural*: por tópico (pertencimento), por tempo, por
  proveniência. Leitura seletiva sobre hierarquia explícita.
- **Delega** o recall *semântico denso*: busca vetorial (HNSW) **não** é feita
  aqui. O envelope pode *referenciar* um índice vetorial; o BH convoca o
  especialista, não compete com ele. Esta é a fronteira deliberada — o `.bh`
  faz o que os formatos compactos não fazem (navegar), e chama quem faz melhor
  o que ele não faz (semântica densa).

## Rodar

```
X:/miniconda3/python.exe X:/bitH/bhmem/demo.py        # demo medida → RESULTS_BHMEM_DEMO.md
X:/miniconda3/python.exe -m pytest X:/bitH/bhmem/tests/ -q   # correção como portão (9/9)
```

## Estado

Protótipo **mínimo e usável** — não é um produto. Faz o loop completo
(escrever → gravar → ler pelas múltiplas leituras → medir) com correção
testada. Próximos passos naturais, se virar produto: append incremental (sem
reescrever o arquivo), índice vetorial referenciado para recall semântico,
hierarquia de tópicos com mais de um nível, e compactação por bloco
(delegando ao especialista, como manda a tese).
