"""Onde a refatoração auto-descritiva (BH) ganha do base-fixa (WebP)?

Varre a fração de conteúdo FOTOGRÁFICO (denso) vs ESTRUTURADO (plano+gradiente+
texto). Acha o cruzamento. Honesto: o teste anterior (25% foto) o BH PERDEU;
aqui medimos a curva inteira p/ achar onde refatorar-com-regra-adaptativa vence.
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
from bhc import decode_full, encode
from bhc.metrics import psnr

S = 1024


def structured(side):
    """Conteúdo estruturado: terço plano, terço gradiente, terço UI/texto."""
    img = np.zeros((side, side, 3), dtype=np.uint8)
    t = side // 3
    img[:t] = (235, 238, 242)
    img[t:2 * t] = corpus.gradient(side, side)[t:2 * t]
    img[2 * t:] = ui_screenshot(side, side)[2 * t:side]
    return img


def composed(photo_frac):
    """Imagem S×S: coluna esquerda estruturada, direita foto, na fração dada."""
    img = structured(S)
    w_photo = int(S * photo_frac)
    if w_photo > 0:
        photo = np.asarray(Image.fromarray(corpus.load_image(
            str(ROOT / "data/corpus/natural_city.jpg"))).resize((S, S), Image.LANCZOS), np.uint8)
        img[:, S - w_photo:] = photo[:, S - w_photo:]
    return img


def webp_at(img, target, fmt="WEBP"):
    pil = Image.fromarray(img); best = None
    for q in range(5, 96, 5):
        b = io.BytesIO(); pil.save(b, fmt, quality=q)
        dec = np.asarray(Image.open(io.BytesIO(b.getvalue())).convert("RGB"))
        p = psnr(img, dec)
        if best is None or abs(p - target) < abs(best[2] - target):
            best = (q, b.tell(), p)
    return best


def main():
    L = ["# REFATORAÇÃO ADAPTATIVA vs BASE-FIXA — varredura por fração de foto\n"]
    L.append(f"Imagem {S}×{S}, threshold BH=16. Esquerda estruturada (plano+gradiente+"
             "texto), direita foto natural. Mede BH/WebP a PSNR igual conforme a foto "
             "cresce.\n")
    L.append("| % foto | BH (KB) | PSNR | WebP (KB) | BH/WebP | veredicto |")
    L.append("|---|---|---|---|---|---|")
    rows = []
    for f in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0):
        img = composed(f)
        blob, _ = encode(img, lossy=True, threshold=16.0, pyramid=False)
        out, _ = decode_full(blob); p = psnr(img, out)
        _, w, _ = webp_at(img, p)
        ratio = len(blob) / w
        verdict = "GANHA" if ratio < 1 else "perde"
        rows.append((f, len(blob), p, w, ratio, verdict))
        L.append(f"| {f:.0%} | {len(blob)/1e3:.1f} | {p:.1f} | {w/1e3:.1f} | "
                 f"**{ratio:.2f}×** | {verdict} |")

    # acha o cruzamento
    cross = None
    for i in range(1, len(rows)):
        if rows[i - 1][4] < 1 <= rows[i][4]:
            cross = (rows[i - 1][0], rows[i][0])
            break

    L.append("\n## LEITURA HONESTA (o número refutou a hipótese)\n")
    pure = rows[0]
    L.append(f"- **O BH PERDE em TODAS as frações — inclusive a 0% de foto** "
             f"(estruturado puro: {pure[4]:.1f}× pior que o WebP). Não há cruzamento. A "
             f"hipótese 'refatorar-com-regra-adaptativa ganha no heterogêneo' está "
             f"REFUTADA.")
    L.append("- **Por quê (o diagnóstico):** (1) a parte de TEXTO/UI explode a quadtree "
             "— cada borda nítida subdivide em folhas minúsculas, e o BH incha; (2) o "
             "ENTROPY CODING do WebP — que o BH não tem — já torna plano, texto e "
             "gradiente quase grátis, então NÃO existe o 'desperdício de base fixa' que "
             "imaginámos recuperar; (3) o entropy coding é o componente mais importante "
             "de um codec, e o BH não o tem.")
    L.append("- **O 48× no gradiente era um canto, não a regra.** Aquele ganho foi num "
             "gradiente liso PURO — o caso ideal único da rampa. Bastou pôr texto/UI "
             "(estrutura real) para a quadtree explodir e o WebP vencer em tudo.")
    L.append("- **A meta-conclusão honesta:** o CODEC é o pior campo para testar a tese "
             "da refatoração. Codec de imagem é máximamente entrincheirado, dependente "
             "de entropy coding, e o dado é PERCEPTUAL (o menos composicional que existe). "
             "A tese 'payload enxuto + regras explícitas' está certa em princípio (o "
             "JPEG a prova), mas para VENCER ali é preciso a maquinaria de entropy — e "
             "ter essa maquinaria = virar um codec normal. Testámos a tese, de novo, no "
             "seu pior terreno: imagem perceptual.")
    L.append("- **O lar da refatoração-composicional NÃO é imagem** — é dado SIMBÓLICO/"
             "estruturado onde a composição é explícita e não há jogo de entropy-coding-"
             "de-pixels a perder. Volta ao mesmo lugar: Intent AI, não codec.")

    out_p = ROOT / "RESULTS_HETEROGENEO.md"
    out_p.write_text("\n".join(L) + "\n", encoding="utf-8")
    for f, b, p, w, r, v in rows:
        print(f"foto={f:.0%}: BH={b/1e3:.1f}KB @{p:.1f}dB  WebP={w/1e3:.1f}KB  {r:.2f}× {v}")
    print(f"relatório: {out_p}")


if __name__ == "__main__":
    main()
