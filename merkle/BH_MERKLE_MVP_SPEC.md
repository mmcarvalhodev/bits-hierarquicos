# BH MERKLE — SPEC DO MVP
## Terceiro terreno: Bits Hierárquicos aplicados a VERIFICAÇÃO

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Origem:** `../arquitetura_bits_hierarquicos.md` + codec + banco
**Status:** SPEC — fecha a trilogia represent → query → verify

---

## 0. POR QUE ESTE PoC EXISTE

Codec provou o paradigma para COMPACTAR. Banco, para CONSULTAR. Falta a
terceira face — VERIFICAR — para que "não é um algoritmo, é uma forma de
ler dados" tenha três domínios sem relação entre si dizendo o mesmo.

```
1. CODEC  → ler para COMPACTAR  (interpretação casa com o conteúdo)
2. BANCO  → ler para CONSULTAR  (interpretação casa com a query)
3. MERKLE → ler para VERIFICAR  (interpretação casa com a prova)
```

**Nota de honestidade prévia:** criptografia tem duas faces.
- CONFIDENCIALIDADE (cifrar p/ esconder): PÉSSIMO encaixe — o ciphertext
  deve ser indistinguível de ruído; estrutura interpretável = cifra
  quebrada. Não construímos isso.
- INTEGRIDADE/AUTENTICAÇÃO (Merkle): encaixe PERFEITO — é literalmente um
  BH, onde o agregado do nó é um hash dos filhos.

A árvore de Merkle JÁ existe (blockchain, git, Certificate Transparency).
O PoC não inventa cripto. Prova a UNIFICAÇÃO: a prova de Merkle é a mesma
leitura-por-objetivo-sobre-hierarquia-grátis que o decode progressivo
(codec) e a poda de agregação (banco).

---

## 1. O MAPEAMENTO

```
nó carrega cor média / min-max  → nó carrega HASH dos filhos
raiz da pirâmide                → ROOT = commitment de todo o dataset
thumbnail (lê o topo)           → COMMITMENT: 1 hash prova a integridade de N itens
ROI (lê um ramo)                → PROVA DE PERTENÇA: O(log n) hashes irmãos
decode progressivo / diff       → LOCALIZAR ADULTERAÇÃO: desce só o ramo divergente
```

## 2. ALEGAÇÕES FALSIFICÁVEIS

Métrica primária: **bytes/hashes lidos ou transmitidos** para a tarefa
(o análogo do "bytes lidos" do codec e "linhas lidas" do banco).

```
M1 — COMMITMENT É O(1)  (≈ thumbnail)
     A integridade do dataset INTEIRO cabe num hash (32 B), independente de N.
     Sucesso: tamanho do root constante com N crescente.

M2 — PROVA DE PERTENÇA É O(log n)  (≈ ROI)
     Provar que o item i pertence ao conjunto comprometido custa log2(N)
     hashes irmãos — não revelar os N itens.
     Sucesso: prova cresce logaritmicamente; ganho ~ N / log N sobre o
     baseline ingênuo (transmitir os N).

M3 — LOCALIZAR ADULTERAÇÃO É O(log n)  (≈ diff progressivo)
     Dado um dataset possivelmente adulterado, achar QUAL item mudou lendo
     só o caminho divergente da raiz à folha.
     Sucesso: nós lidos = O(log n) vs O(n) do re-hash total.

M_BORDA — A FRONTEIRA DECLARADA  (≈ textura natural / valor independente)
     - Verificação TOTAL (auditar todos os itens) lê tudo → sem ganho.
     - Custo de armazenamento: a árvore ~dobra o nº de hashes (overhead).
     - Merkle dá INTEGRIDADE, não confidencialidade.
     Esperado, medido, não escondido.
```

## 3. ESTRUTURA

```
Árvore de Merkle binária sobre N folhas (itens-registo).
  folha    = H_leaf(item)            com prefixo 0x00 (domain separation)
  interno  = H_node(esq || dir)      com prefixo 0x01 (anti second-preimage)
  root     = commitment
  hash     = SHA-256
Padding até potência de 2 com folha-sentinela; n real registado.
```

## 4. AS TRÊS LEITURAS (mesma árvore, objetivo diferente)

```
commit()        → lê só a raiz (1 hash)
prove(i)        → lê um ramo (log n hashes irmãos)
locate_tamper() → desce o ramo divergente (log n)
full_audit()    → lê todas as folhas (o baseline interno)
```

## 5. BASELINES

```
Prova ingênua de pertença:  transmitir os N itens (ou N hashes) p/ o
                            verificador recomputar o root.
Localização ingênua:        re-hashear os N itens e comparar.
```

## 6. VEREDICTO

Por alegação: CONFIRMADA / PARCIAL / REFUTADA, com bytes medidos.
Tabela de escala: N de 2^10 a 2^20 → prova log-linear.
M_BORDA reportada como fronteira, não falha.

## 7. ESTRUTURA DO PROJETO

```
merkle/
├── BH_MERKLE_MVP_SPEC.md
├── src/
│   ├── bhmerkle/tree.py     # MerkleTree: build/commit/prove/verify/locate
│   └── bench/harness.py     # M1-M3 + escala, emite RESULTS.md
├── tests/
│   ├── test_correctness.py  # verify(prove(i)); tamper muda root; localização exata
│   └── test_reads.py        # M1 O(1); M2 O(log n); M3 O(log n); borda lê tudo
└── RESULTS.md
```

Stack: Python 3.13 + hashlib (SHA-256). Standalone. Gate: correção cripto
(prova válida verifica; prova adulterada falha; localização exata) antes
de medir.

---

*O codec leu pixels pela convenção que minimiza bytes×erro. O banco, linhas
pela que minimiza linhas×query. O Merkle lê hashes pela que minimiza
prova×confiança. Mesma moldura, três objetivos. Não é o algoritmo — é a
forma de ler.*
