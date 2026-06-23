# bhmem — memória de agente como .bh (demo medida)

- memórias: **2250** · tópicos: **60**
- arquivo `.bh`: **661,480 bytes** · plano JSONL: **592,135 bytes**

## Cada leitura lê só o que precisa (bytes REAIS lidos do arquivo)

A linha de base plana lê o arquivo **inteiro** para qualquer consulta (592,135 B). O `.bh` lê só o ramo pedido.

| leitura | o que devolve | bytes lidos | % do arquivo | vs plano |
|---|---|---|---|---|
| `summary()` | resumo de todos os tópicos (60) | 16,490 B | 2.5% | **36× menos** |
| `recall('review_07')` | as memórias do tópico (39) | 26,743 B | 4.0% | **22× menos** |
| `since(últ. 5d)` | memórias recentes (40) | 64,873 B | 9.8% | **9× menos** |
| `provenance('m00000')` | fonte+caminho de 1 memória (1) | 71,427 B | 10.8% | **8× menos** |
| `full()` | tudo (linha de base) (2250) | 661,480 B | 100.0% | **1× menos** |

## O que isto demonstra

- **Não é mais um número de compressão.** É a CAPACIDADE: o agente lê o resumo, um tópico, uma janela ou a proveniência **sem carregar a memória inteira**. O custo de cada leitura é proporcional ao que ela pede.
- **A estrutura é parte do formato.** Pertencimento (tópico), tempo e proveniência são navegáveis no próprio arquivo — não em quatro sistemas colados por cima.
- **Fronteira honesta.** Recall *semântico denso* (vetorial) não é feito aqui — delega-se a um índice HNSW que o envelope referencia. O `.bh` convoca o especialista; não compete com ele.
