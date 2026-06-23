# MULTIMODAL — FATIA 1 (STORAGE): substrato unificado vs pilha costurada

Ativo co-registrado 256×256 (RGB+depth+seg+embeddings por região). Pilha costurada = storage(3 arquivos) + HNSW + thumbnail + índice espacial. Unificado = 1 hierarquia (preview e índice espacial FREE).

Varre d (dim do embedding): d pequeno → estrutura/índice pesam → unificado ganha mais; d grande → embeddings dominam (Shannon) → empata.

| d (emb) | nº regiões | costurado | unificado | ganho |
|---|---|---|---|---|
| 8 | 577 | 110.4 KB | 27.7 KB | **3.99×** |
| 32 | 577 | 165.8 KB | 101.5 KB | **1.63×** |
| 64 | 577 | 239.6 KB | 199.9 KB | **1.20×** |
| 128 | 577 | 387.4 KB | 396.8 KB | **0.98×** |
| 256 | 577 | 682.8 KB | 790.5 KB | **0.86×** |

## Breakdown (d=64) — onde o unificado economiza

| componente | costurado | unificado |
|---|---|---|
| struct(3×) → struct(1×) | 576 B | 192 B |
| payload → payload | 2.9 KB | 2.9 KB |
| embeddings → embeddings | 147.7 KB | 147.7 KB |
| HNSW → emb_summary | 73.9 KB | 49.2 KB |
| thumbnail → thumbnail | 3.1 KB | 0 B |
| spatial_idx → spatial_idx | 11.5 KB | 0 B |

## LEITURA HONESTA

- **O ganho depende de quanto os embeddings dominam.** d pequeno: 3.99× (estrutura+índice+rendition pesam, unificado ganha). d grande: 0.86× (embeddings dominam — Shannon paga igual dos dois lados — o ganho encolhe). É a mesma lição do wafer: payload domina → estrutura partilhada rende pouco.
- **SINAL NEGATIVO p/ produto-de-storage:** o cruzamento é em d≈96-128, mas embeddings de IA modernos são d=768–4096. Nesse regime real, o unificado PERDE em storage — porque o resumo-de-embedding no nó custa O(n_internos × d), que cresce com d, enquanto o grafo HNSW é O(n × M), constante em d. Storage NÃO é o ângulo de produto em embeddings reais.
- **Ressalva:** o índice unificado aqui é ingênuo (centroide d-dim em todo nó interno). Um resumo projetado/baixa-dim para poda poderia recuperar — mas é não-medido. Não vendas storage; o ângulo, se existir, é acesso+ops.
- **O que o unificado elimina de verdade:** as 3 estruturas viram 1; o thumbnail (rendition) some (preview é free); o índice espacial some (a hierarquia É o índice). O HNSW vira resumo-de-embedding no nó.
- **A fronteira:** se a carga for retrieval GLOBAL (não escopado), o HNSW volta a ser preciso e o unificado não o substitui. E conteúdo não-co-registrado faria a união super-subdividir (fronteira W3).
- **Fatia 1 mede STORAGE.** O valor de produto real inclui acesso (fatia 2), temporal/vídeo (fatia 3) e $ de operação (fatia 4) — e a simplicidade de 1 sistema vs 4, que não cabe num número mas é metade do argumento.
