# MULTIMODAL — CORREÇÃO: embedding PROGRESSIVO vs injeção ingênua

Nó interno guarda prefixo p=64 (Matryoshka), folha guarda full d. Compara o veredicto de storage ANTES (ingênuo) e DEPOIS (progressivo).

| d | costurado | unif. INGÊNUO | ganho | unif. PROGRESSIVO | ganho |
|---|---|---|---|---|---|
| 64 | 239.6 KB | 199.9 KB | 1.20× | 199.9 KB | **1.20×** |
| 256 | 682.8 KB | 790.5 KB | 0.86× | 643.1 KB | **1.06×** |
| 768 | 1.86 MB | 2.37 MB | 0.79× | 1.82 MB | **1.02×** |
| 1024 | 2.46 MB | 3.15 MB | 0.78× | 2.42 MB | **1.02×** |
| 4096 | 9.55 MB | 12.60 MB | 0.76× | 9.51 MB | **1.00×** |

## LEITURA HONESTA

- **A correção MOVE o veredicto.** O probe ingênuo perdia a partir de d≈128 porque cobrava full-d em cada nó interno. Com prefixo Matryoshka, o índice interno cai ~d/p× e o unificado volta a empatar/ganhar mesmo em d=1024-4096. O 'payload afoga' era em parte artefato da injeção ingênua.
- **MAS o ganho é só no ÍNDICE, não no bulk.** Os embeddings de folha (o grosso) são iguais dos dois lados — ambos guardam o canônico uma vez (Shannon de verdade). O unificado só ganha porque seu índice (prefixos internos) é mais barato que o HNSW+espacial+thumbnail. Ganho real, pequeno em absoluto.
- **E o SOTA já explora a redundância:** Matryoshka e PQ existem e são estado da arte. 'Embedding é compressível/hierárquico' é verdade — e já está implantado. O único que permanece aberto é a UNIFICAÇÃO: o mesmo prefixo servindo de embedding-progressivo E índice E estrutura, numa peça só, em vez de Matryoshka + HNSW + layout separados.
- **Conclusão corrigida:** a Lei 6 não estava errada, mas eu a apliquei mal — tratei infraestrutura compressível como payload. Corrigido, o storage passa de 'perde' para 'empata/ganha marginal no índice'. Reabre a porta uma fresta; não a escancara. O bulk (embedding de folha) continua sendo um empate de Shannon — lá ninguém ganha.
