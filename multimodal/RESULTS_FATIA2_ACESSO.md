# MULTIMODAL — FATIA 2 (ACESSO): bytes movidos por query

Ativo 256×256, 577 regiões, embedding d=768 (IA real), HNSW efSearch=64. Métrica: bytes movidos por query.

| query | BH unificado | pilha costurada | ganho | nota |
|---|---|---|---|---|
| Q1 preview ~32px | 402 B | 3.1 KB | **7.6×** | ambos pequenos |
| Q2 ROI 64² + camadas | 276 B | 568 B | **2.1×** | estrutura partilhada |
| Q3 retrieval escopado | 141.3 KB | 204.8 KB | **1.4×** | janela=46 folhas vs ef=64 |
| Q3b retrieval janela grande | 875.5 KB | 204.8 KB | **0.23× (perde)** | janela=285 > ef=64 → perde |
| Q4 agregado de janela | 72 B | 230 B | **3.2×** | agregado pronto no nó |

## LEITURA HONESTA

- **Q4 (agregado) e Q2 (ROI): o BH ganha por construção** — o agregado já está no nó (não varre a janela); a estrutura partilhada serve as 3 camadas numa travessia só. É o mesmo ganho do banco e do codec, num ativo multimodal.
- **Q3 (retrieval) é o divisor — e confirma a Lei 6.** Em janela PEQUENA, a poda espacial deixa poucas folhas e o BH lê menos embeddings que o efSearch do HNSW → ganha. Em janela GRANDE (Q3b), o nº de folhas ultrapassa o efSearch e o BH PERDE — porque aí o payload (embeddings d=768) domina e ler todos os candidatos custa mais que a busca do HNSW.
- **O padrão de novo:** o BH ganha onde a resposta é ESTRUTURAL (agregado, região, janela escopada pequena) e perde onde o EMBEDDING DENSO domina (retrieval de janela larga / global). Lei 6, mais uma vez.
- **Veredicto da fatia 2:** acesso é MISTO — vitórias reais em agregado/ROI/retrieval-escopado-estreito; derrota em retrieval largo/global (onde o HNSW reina). Não é o ganho universal que viraria produto sozinho; é mais um voto para 'o valor é operacional, não de números'.
