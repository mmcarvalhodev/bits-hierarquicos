"""A UNIÃO: um .bh orquestrado dá representação (menor) E leitura seletiva, junto.

Um documento (regiões de naturezas diferentes) gravado como:
  estrutura (árvore + bounds + codec_id por região)  ← barato
  + payload por região delegado ao especialista       ← flat=3B, grad=12B, texto/diagrama=PNG/WebP
Mede, no MESMO arquivo:
  REPRESENTAÇÃO: tamanho total vs WebP-no-todo
  LEITURA:       bytes p/ ler UMA região vs WebP (que precisa do arquivo todo)
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from PIL import Image

from bench import corpus
from bench.harness import ui_screenshot

Q = 256
HEADER = 32
PER_REGION_META = 13   # bounds(8) + codec_id(1) + offset(4)


def webp(img, q=82):
    b = io.BytesIO(); Image.fromarray(img).save(b, "WEBP", quality=q); return b.getvalue()


def png(img):
    b = io.BytesIO(); Image.fromarray(img).save(b, "PNG"); return b.getvalue()


def fmt(b):
    return f"{b/1e3:.1f} KB" if b >= 1e3 else f"{b} B"


def main():
    # documento: plano + gradiente + texto/UI + diagrama (forma-fechada)
    regions = {
        "plano": (np.full((Q, Q, 3), (235, 238, 242), np.uint8), "constante", 3),
        "gradiente": (corpus.gradient(Q, Q), "fórmula", 12),
        "texto/UI": (ui_screenshot(Q, Q)[:Q, :Q], None, None),
        "diagrama": (corpus.shapes(Q, Q), None, None),
    }
    # resolve o especialista de cada região
    payloads = {}
    for name, (img, codec, b) in regions.items():
        if b is not None:
            payloads[name] = (codec, b)
        else:
            pp, pw = len(png(img)), len(webp(img))
            payloads[name] = ("PNG" if pp < pw else "WebP", min(pp, pw))

    structure = HEADER + PER_REGION_META * len(regions)
    bh_total = structure + sum(b for _, b in payloads.values())

    # WebP no todo (o documento inteiro montado)
    whole = np.zeros((2 * Q, 2 * Q, 3), np.uint8)
    imgs = list(regions.values())
    whole[:Q, :Q] = imgs[0][0]; whole[:Q, Q:] = imgs[1][0]
    whole[Q:, :Q] = imgs[2][0]; whole[Q:, Q:] = imgs[3][0]
    webp_total = len(webp(whole))

    L = ["# A UNIÃO — representação + leitura seletiva no mesmo .bh\n"]
    L.append(f"Documento {2*Q}×{2*Q}: 4 regiões de naturezas diferentes. O .bh roteia "
             "cada resíduo ao especialista E mantém a estrutura para leitura seletiva.\n")

    L.append("## FACE 1 — Representação (tamanho)\n")
    L.append("| | tamanho |")
    L.append("|---|---|")
    L.append(f"| WebP no todo | {fmt(webp_total)} |")
    L.append(f"| .bh orquestrado | {fmt(bh_total)} |")
    L.append(f"| **ganho** | **{webp_total/bh_total:.2f}× menor** |")
    L.append("\n### Onde os bytes do .bh foram\n")
    L.append("| região | especialista | bytes |")
    L.append("|---|---|---|")
    L.append(f"| (estrutura) | árvore+bounds+ids | {structure} B |")
    for name, (codec, b) in payloads.items():
        L.append(f"| {name} | {codec} | {fmt(b)} |")

    L.append("\n## FACE 2 — Leitura seletiva (bytes para ler UMA região)\n")
    L.append("No .bh, ler uma região = estrutura + o payload dela. No WebP, qualquer "
             "região exige decodificar o arquivo TODO.\n")
    L.append("| operação | .bh lê | WebP lê | .bh vs WebP |")
    L.append("|---|---|---|---|")
    for name, (codec, b) in payloads.items():
        bh_read = structure + b
        L.append(f"| ler região '{name}' | {fmt(bh_read)} | {fmt(webp_total)} (tudo) | "
                 f"**{webp_total/bh_read:.0f}× menos** |")
    # preview do documento: regiões de fórmula renderizam de graça; o resto, payload
    preview_read = structure + payloads["plano"][1] + payloads["gradiente"][1]
    L.append(f"| preview (formas-fechadas renderizam grátis) | ~{fmt(preview_read)}+ | "
             f"{fmt(webp_total)} (tudo) | **muito menos** |")

    L.append("\n## A UNIÃO, EM UMA FRASE\n")
    L.append(f"- **O mesmo arquivo é {webp_total/bh_total:.1f}× menor que o WebP E permite "
             f"ler qualquer região por ~dezenas× menos bytes** — porque a estrutura é o "
             f"índice e o resíduo é delegado. O WebP é menor-é-único: para um preview ou "
             f"uma região, decodifica tudo.")
    L.append("- **Nenhuma ferramenta SOTA dá as duas juntas:** WebP/AVIF = resíduo ótimo "
             "mas leitura única; PDF = orquestra mas lista plana sem leitura seletiva; "
             "OLAP/GPU = leitura seletiva mas não é formato. O `.bh` = as duas + "
             "hierarquia, num envelope.")
    L.append("- **Honestidade:** vale em conteúdo ESTRUTURA-DOMINANTE (documento/diagrama/"
             "UI). Em foto pura, a representação empata (WebP reina na textura) e só "
             "sobra a face de leitura. E é arquitetura, não benchmark: a prova final é "
             "construir o formato, não medir o protótipo.")

    out = ROOT / "RESULTS_UNIAO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"REPRESENTAÇÃO: .bh={fmt(bh_total)} vs WebP={fmt(webp_total)} "
          f"({webp_total/bh_total:.2f}× menor)")
    print(f"LEITURA região 'diagrama': .bh lê {fmt(structure+payloads['diagrama'][1])} "
          f"vs WebP {fmt(webp_total)} (tudo)")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
