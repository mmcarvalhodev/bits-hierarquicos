# DÍVIDA ARQUITETURAL — decomposição de um stack RAG real

Corpus: 10,000,000 chunks × 512 B · embedding d=1024. Classificação conservadora (dúvida → irredutível). Régua: 50-70% dívida = produto; 10-20% = filosofia.

## Componentes (caso COM duplicação de embeddings — pior caso de dívida)

| componente | tamanho | classe | porquê |
|---|---|---|---|
| texto cru (chunks) | 5.1 GB | IRR | payload — o dado em si |
| embeddings canônicos | 41.0 GB | IRR | info semântica; custo do padrão de acesso 'similaridade' (Lei 6: payload) |
| grafo HNSW | 2.6 GB | IRR | índice de similaridade — padrão de acesso real (no-free-lunch) |
| índice keyword (BM25) | 2.0 GB | IRR | padrão de acesso DIFERENTE (busca lexical) — organização incompatível |
| índice de metadados | 0.5 GB | IRR | padrão de acesso 'filtro' — organização própria |
| cópia de vetores no índice | 41.0 GB | ELIM | duplicação dos embeddings p/ localidade — eliminável (índice referencia o canônico) |
| duplicação doc-store↔search | 5.1 GB | ELIM | o chunk vive no object store E no motor de busca — duplicação |
| cache de query/embedding | 2.0 GB | ELIM | derivado, recomputável |
| previews/resumos derivados | 1.0 GB | ELIM | derivado do texto, recomputável |

**Total 100.3 GB · irredutível 51.1 GB · dívida 49.1 GB → DÍVIDA = 49%**

## Sensibilidade — o swing-factor é a duplicação de embeddings

| cenário | total | dívida | % dívida |
|---|---|---|---|
| COM duplicação de vetores | 100.3 GB | 49.1 GB | **49%** |
| SEM duplicação (índice referencia canônico) | 59.3 GB | 8.2 GB | **14%** |

| d (embedding) | % dívida (com dup) | % dívida (sem dup) |
|---|---|---|
| 256 | 45% | 25% |
| 768 | 48% | 16% |
| 1024 | 49% | 14% |
| 4096 | 51% | 8% |

## LEITURA HONESTA

- **A dívida é REAL mas BORDERLINE: ~25-49%**, e o swing é se o stack duplica os embeddings (vetores no índice + no store). Com duplicação, beira os 50% (produto); sem, cai para ~25% (zona cinzenta).
- **Ironia da Lei 6:** a maior fatia de DÍVIDA é a duplicação dos EMBEDDINGS — payload denso, não estrutura. Ou seja, a dívida eliminável também é dominada por payload. E o SOTA já a ataca (índices em disco, quantização, pgvector que referencia em vez de copiar).
- **A parte de estrutura pura (caches, previews, metadados) é PEQUENA** (<10%). O 'oito subsistemas porque o dado nasceu burro' é menos dívida de bytes do que parece — a maior parte do custo é payload irredutível + índices necessários por padrões de acesso diferentes (no-free-lunch).
- **O que ISTO não captura:** a dívida OPERACIONAL (sync, drift, engenharia de manter N sistemas) não cabe em bytes — e é real. Em custo de bytes a dívida é ~25-49%; em custo de OPERAÇÃO pode ser maior, mas isso não é mensurável por este modelo (só construindo e operando).
- **Veredicto pela régua do autor:** em BYTES, a dívida fica na fronteira (25-49%), não nos 50-70% que cravariam um produto. O caso de bytes é borderline-fraco; o caso forte, se existir, é operacional — e esse este modelo não mede.
