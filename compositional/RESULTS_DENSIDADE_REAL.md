# DENSIDADE REAL DE EMBEDDINGS — a Lei 6 sobre dado do mundo

6,000 palavras PT reais · modelo all-MiniLM-L6-v2 · dim nominal d=384. PCA: componentes p/ capturar X% da variância.

| variância capturada | dimensões necessárias | fração de d |
|---|---|---|
| 80% | 106 | 28% |
| 90% | 160 | 42% |
| 95% | 211 | 55% |
| 99% | 301 | 78% |

## LEITURA HONESTA

- **O embedding NÃO é tão denso quanto nominal.** 160 dimensões capturam 90% da variância — 42% das 384. O 'payload denso irredutível' que eu cobrei era inflado: ~224 dimensões são quase redundância linear. Confirma, em dado REAL, o que o Márcio disse: tratei infraestrutura compressível como payload.
- **Mas isto é compressibilidade LINEAR, não composicionalidade.** PCA mede que o vetor vive perto de um subespaço de ~160d — é o que Matryoshka/PQ já exploram. NÃO prova que o significado seja composto de primitivos simbólicos. Reduz o payload ~2.4×; não o transforma numa equação.
- **O que muda na conclusão:** a 'derrota' do BH em embeddings era em parte por eu cobrar 384d quando ~160d bastam. Com o embedding na sua dimensão real, a margem aperta — mas o bulk continua sendo um vetor (conexionista), não uma composição (simbólica). A densidade real fica ENTRE 'irredutível' e 'composto': compressível ~2.4×, mas não nulo.
- **A pergunta de fundo segue aberta e NÃO é deste experimento:** quanto do SIGNIFICADO (não da geometria do vetor) é composicional? Isso é a aposta do Intent AI, e décadas de NLP não a fecharam. Um script não fecha.
