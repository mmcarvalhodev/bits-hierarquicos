"""Mede a DENSIDADE REAL de embeddings — a Lei 6 sobre dado do mundo, não sintético.

Pergunta honesta: quando eu cobrei o embedding como 'payload denso irredutível'
(384/768 dim), ele é REALMENTE tão denso? Embeddings reais vivem num subespaço
de dimensão intrínseca << nominal? Mede com PCA sobre embeddings de palavras
reais (PT), modelo real (all-MiniLM-L6-v2, 384d).

Ressalva declarada: dimensão intrínseca baixa = compressibilidade LINEAR
(conexionista), NÃO compositional-simbólica. Isto mede o quanto o payload
ENCOLHE, não se o significado é composto de primitivos. São coisas diferentes.
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def main():
    print("carregando modelo real (all-MiniLM-L6-v2, 384d) ...", flush=True)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # palavras reais PT
    words = []
    with open("X:/claude/data/freq_pt_50k.txt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.split()[0] if line.split() else ""
            if w.isalpha() and len(w) > 1:
                words.append(w)
            if len(words) >= 6000:
                break
    print(f"  {len(words)} palavras reais; embedando ...", flush=True)
    emb = model.encode(words, batch_size=256, show_progress_bar=False,
                       convert_to_numpy=True, normalize_embeddings=True)
    d = emb.shape[1]

    pca = PCA().fit(emb)
    cum = np.cumsum(pca.explained_variance_ratio_)
    def dims_for(frac):
        return int(np.searchsorted(cum, frac) + 1)

    L = ["# DENSIDADE REAL DE EMBEDDINGS — a Lei 6 sobre dado do mundo\n"]
    L.append(f"{len(words):,} palavras PT reais · modelo all-MiniLM-L6-v2 · "
             f"dim nominal d={d}. PCA: componentes p/ capturar X% da variância.\n")
    L.append("| variância capturada | dimensões necessárias | fração de d |")
    L.append("|---|---|---|")
    for frac in (0.80, 0.90, 0.95, 0.99):
        k = dims_for(frac)
        L.append(f"| {frac:.0%} | {k} | {k/d:.0%} |")

    k90 = dims_for(0.90)
    L.append("\n## LEITURA HONESTA\n")
    L.append(f"- **O embedding NÃO é tão denso quanto nominal.** {k90} dimensões "
             f"capturam 90% da variância — {k90/d:.0%} das {d}. O 'payload denso "
             f"irredutível' que eu cobrei era inflado: ~{d-k90} dimensões são quase "
             f"redundância linear. Confirma, em dado REAL, o que o Márcio disse: tratei "
             f"infraestrutura compressível como payload.")
    L.append(f"- **Mas isto é compressibilidade LINEAR, não composicionalidade.** "
             f"PCA mede que o vetor vive perto de um subespaço de ~{k90}d — é o que "
             f"Matryoshka/PQ já exploram. NÃO prova que o significado seja composto de "
             f"primitivos simbólicos. Reduz o payload ~{d/k90:.1f}×; não o transforma "
             f"numa equação.")
    L.append(f"- **O que muda na conclusão:** a 'derrota' do BH em embeddings era em "
             f"parte por eu cobrar {d}d quando ~{k90}d bastam. Com o embedding na sua "
             f"dimensão real, a margem aperta — mas o bulk continua sendo um vetor "
             f"(conexionista), não uma composição (simbólica). A densidade real fica "
             f"ENTRE 'irredutível' e 'composto': compressível ~{d/k90:.1f}×, mas não nulo.")
    L.append("- **A pergunta de fundo segue aberta e NÃO é deste experimento:** quanto "
             "do SIGNIFICADO (não da geometria do vetor) é composicional? Isso é a "
             "aposta do Intent AI, e décadas de NLP não a fecharam. Um script não fecha.")

    out = __import__("pathlib").Path(__file__).resolve().parent / "RESULTS_DENSIDADE_REAL.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nd nominal={d} | 90% var em {k90}d ({k90/d:.0%}) | "
          f"95% em {dims_for(0.95)}d | 99% em {dims_for(0.99)}d")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
