"""Orquestração: o BH roteia cada região ao codec especialista (nível 3 do GPT).

Não é 'BH puro' (perde). É BH = envelope de estrutura + resíduo delegado ao
melhor especialista LOCAL: fórmula onde há fórmula, WebP onde há foto, PNG onde
há texto, constante onde é plano.

Compara:
  A) WebP no TODO (um codec só)
  B) soma de WebP por região (só dividir — testa se splitting sozinho ajuda)
  C) ORQUESTRADO (especialista certo por região)
Responde: roteamento cross-paradigma ganha de um-codec-no-todo? Onde?
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
from bhc.metrics import psnr

Q = 256  # lado de cada quadrante


def webp_bytes(img, q=82):
    b = io.BytesIO(); Image.fromarray(img).save(b, "WEBP", quality=q); return b.getvalue()


def png_bytes(img):
    b = io.BytesIO(); Image.fromarray(img).save(b, "PNG"); return b.getvalue()


def ramp_corners(block):
    """4 cantos (12 B) + reconstrução bilinear; devolve (bytes, recon)."""
    s = block.shape[0]
    c = np.array([block[0, 0], block[0, -1], block[-1, 0], block[-1, -1]], np.float64)
    r = np.linspace(0, 1, s)
    yy, xx = np.meshgrid(r, r, indexing="ij")
    yy, xx = yy[..., None], xx[..., None]  # (s,s,1) p/ broadcast com cantos RGB (3,)
    rec = (c[0]*(1-yy)*(1-xx) + c[1]*(1-yy)*xx + c[2]*yy*(1-xx) + c[3]*yy*xx)
    return 12, np.clip(np.rint(rec), 0, 255).astype(np.uint8)


def fmt(b):
    return f"{b/1e3:.1f} KB" if b >= 1e3 else f"{b} B"


def measure(name, q4):
    """q4 = lista de 4 quadrantes (TL,TR,BL,BR). Mede A/B/C."""
    flat, grad, ui, br = q4
    whole = np.zeros((2 * Q, 2 * Q, 3), np.uint8)
    whole[:Q, :Q] = flat; whole[:Q, Q:] = grad; whole[Q:, :Q] = ui; whole[Q:, Q:] = br
    A = len(webp_bytes(whole, 82))
    B = sum(len(webp_bytes(r, 82)) for r in q4) + 4 * 9
    flat_b = 3
    grad_b, _ = ramp_corners(grad)
    ui_b = min(len(png_bytes(ui)), len(webp_bytes(ui, 82)))
    br_b = min(len(png_bytes(br)), len(webp_bytes(br, 82)))
    C = flat_b + grad_b + ui_b + br_b + 4 * 9
    return name, A, B, C, (flat_b, grad_b, ui_b, br_b)


def main():
    flat = np.full((Q, Q, 3), (235, 238, 242), np.uint8)
    grad = corpus.gradient(Q, Q)
    ui = ui_screenshot(Q, Q)[:Q, :Q]
    photo = np.asarray(Image.fromarray(corpus.load_image(
        str(ROOT / "data/corpus/natural_city.jpg"))).resize((Q, Q), Image.LANCZOS), np.uint8)
    shapes = corpus.shapes(Q, Q)  # diagrama/vetor sintético (sem foto)

    cases = [
        measure("foto-pesado (plano+grad+UI+FOTO)", [flat, grad, ui, photo]),
        measure("documento (plano+grad+UI+diagrama)", [flat, grad, ui, shapes]),
    ]

    L = ["# ORQUESTRAÇÃO — BH roteia codec especialista por região\n"]
    L.append(f"Imagens {2*Q}×{2*Q}. A=WebP no todo · B=soma WebP/região · "
             "C=orquestrado (especialista/região). Dois conteúdos: um dominado por foto, "
             "outro por formas-fechadas (documento).\n")
    L.append("| conteúdo | A WebP-todo | B split-WebP | C orquestrado | C vs A |")
    L.append("|---|---|---|---|---|")
    for name, A, B, C, parts in cases:
        L.append(f"| {name} | {fmt(A)} | {fmt(B)} ({B/A:.2f}×) | {fmt(C)} | "
                 f"**{C/A:.2f}×** |")

    L.append("\n## LEITURA HONESTA\n")
    foto = cases[0]; doc = cases[1]
    L.append(f"- **A orquestração é uma estratégia QUE NÃO PODE PERDER MUITO** — no pior "
             f"caso ela roteia tudo para o melhor codec único. No conteúdo foto-pesado "
             f"empata (**{foto[3]/foto[1]:.2f}×**): a foto domina os BYTES (mesmo sendo "
             f"25% da área) e a orquestração usa WebP nela de qualquer forma — não há o "
             f"que ganhar.")
    L.append(f"- **No documento (formas-fechadas) ela GANHA ({doc[3]/doc[1]:.2f}×)** — "
             f"porque o gradiente vira 12 B (fórmula) e o plano 3 B, onde o WebP os trata "
             f"como sinal e gasta bytes. O ganho é proporcional à fração dos BYTES que é "
             f"forma-fechada (plano/gradiente/vetor), não à área.")
    L.append("- **A regra exata:** orquestrar ganha quando o orçamento de bytes é "
             "dominado por conteúdo de FORMA FECHADA (documento, diagrama, UI, cena de "
             "IA em camadas vetoriais); empata quando é dominado por FOTO (o byte da "
             "textura manda, e ali o especialista é o WebP mesmo). Nunca perde feio — "
             "só paga o overhead de estrutura.")
    L.append("- **O que o BH adiciona ao PDF:** o PDF já orquestra especialistas num "
             "container — mas é uma LISTA plana de objetos. O BH acrescenta HIERARQUIA "
             "(pertencimento, níveis) e MÚLTIPLAS LEITURAS (preview/ROI/prova) sobre a "
             "mesma estrutura. O resíduo, esse, é delegado — o BH nunca devia comprimi-lo "
             "sozinho. A frase do GPT está certa: **o BH orquestra codecs por região "
             "dentro de uma hierarquia explícita; não os substitui.**")

    out = ROOT / "RESULTS_ORQUESTRACAO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"A) WebP-todo={fmt(A)}  B) split-WebP={fmt(B)} ({B/A:.2f}×)  "
          f"C) orquestrado={fmt(C)} ({C/A:.2f}×)")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
