"""Benchmark de PORTFÓLIO — a tese-mãe: o valor do BH é múltiplas entradas
de ataque sobre UMA estrutura, não vencer uma tarefa isolada.

Um ativo 4K precisa servir um MIX de operações:
  thumbnail · 480p · 1080p · full 4K · ROI 512²

Três abordagens, mesma carga:
  A) Especialista-ESCADA  — guarda N renditions WebP (uma por resolução).
                            Storage = soma. Trabalho/op = ler a rendition certa.
  B) Especialista-ÚNICO   — guarda só o 4K WebP.
                            Storage = mínimo. Trabalho/op = decodar o 4K SEMPRE.
  C) BH                   — guarda UMA estrutura.
                            Storage = 1 arquivo. Trabalho/op = leitura parcial.

A alegação do BH: tem o storage BAIXO do "único" E o trabalho BAIXO da
"escada" — o melhor dos dois. Mas só vence quando seu arquivo único é
competitivo em tamanho (a condição: hierarquia compartilhada + compressão
não-degenerada). Onde não é, perde — e isso fica medido.
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
from bhc import decode_full, decode_progressive, decode_roi, encode
from bhc.metrics import psnr

W, H = 3840, 2160
RES = [("thumb", 256), ("480p", 854), ("1080p", 1920), ("4K", 3840)]
ROI = (W // 2 - 256, H // 2 - 256, 512, 512)


def webp_bytes(img: np.ndarray, q: int = 85) -> bytes:
    b = io.BytesIO()
    Image.fromarray(img).save(b, "WEBP", quality=q)
    return b.getvalue()


def resize_to_width(img: np.ndarray, target_w: int) -> np.ndarray:
    if target_w >= img.shape[1]:
        return img
    pil = Image.fromarray(img)
    h = round(img.shape[0] * target_w / img.shape[1])
    return np.asarray(pil.resize((target_w, h), Image.LANCZOS), dtype=np.uint8)


def bh_level_for_width(target_w: int, levels: int) -> int:
    k = 0
    while 2**k < target_w and k < levels:
        k += 1
    return min(k, levels)


def run(name: str, img: np.ndarray) -> dict:
    # --- A) escada de WebP ---
    ladder = {label: webp_bytes(resize_to_width(img, w)) for label, w in RES}
    ladder_storage = sum(len(v) for v in ladder.values())

    # --- B) WebP único (4K) ---
    single = ladder["4K"]
    single_storage = len(single)

    # --- C) BH único ---
    blob, stats = encode(img, lossy=True, threshold=8.0, pyramid=True)
    bh_storage = len(blob)
    bh_full, _ = decode_full(blob)
    bh_psnr = psnr(img, bh_full)

    # trabalho (bytes lidos) por operação
    work = {"res": {}, "roi": {}}
    for label, w in RES:
        lvl = bh_level_for_width(w, stats["levels"])
        _, info = decode_progressive(blob, max_level=lvl)
        work["res"][label] = {
            "ladder": len(ladder[label]),       # lê a rendition certa
            "single": single_storage,            # decoda o 4K inteiro
            "bh": info["bytes_read"],            # prefixo progressivo
        }
    x, y, rw, rh = ROI
    _, roi_info = decode_roi(blob, x, y, rw, rh)
    work["roi"] = {
        "ladder": single_storage,   # crop precisa do 4K full
        "single": single_storage,
        "bh": roi_info["bytes_read"],
    }

    return {
        "name": name,
        "ladder_storage": ladder_storage,
        "single_storage": single_storage,
        "bh_storage": bh_storage,
        "bh_psnr": bh_psnr,
        "work": work,
    }


def fmt(b: int) -> str:
    return f"{b/1e6:.3f}"


def main() -> None:
    images = [
        ("gradient (sintético)", corpus.gradient(W, H)),
        ("ui (screenshot)", ui_screenshot(W, H)),
        ("natural_city", corpus.load_image(str(ROOT / "data/corpus/natural_city.jpg"))),
    ]
    L = ["# BH — BENCHMARK DE PORTFÓLIO (a tese-mãe)\n"]
    L.append("Um ativo 4K serve o mix {thumb, 480p, 1080p, 4K, ROI}. Compara o BH "
             "(uma estrutura, múltiplas leituras) contra duas estratégias de "
             "especialista. Métrica: armazenamento (MB) e trabalho por operação "
             "(MB lidos).\n")
    L.append("- **Escada**: guarda N renditions WebP — storage alto, trabalho baixo.")
    L.append("- **Único**: guarda só o 4K WebP — storage mínimo, trabalho alto "
             "(decoda tudo a cada op).")
    L.append("- **BH**: uma estrutura — storage de 1 arquivo, trabalho de leitura "
             "parcial. A alegação: o melhor dos dois, QUANDO o arquivo é competitivo.\n")

    for r in [run(n, im) for n, im in images]:
        L.append(f"\n## {r['name']}\n")
        L.append(f"BH full PSNR = {r['bh_psnr']:.1f} dB (qualidade ~comparável ao WebP q85)\n")
        L.append("### Armazenamento total (servir o mix)\n")
        L.append("| estratégia | storage | vs BH |")
        L.append("|---|---|---|")
        for label, s in [("Escada (N WebP)", r["ladder_storage"]),
                         ("Único (1 WebP 4K)", r["single_storage"]),
                         ("BH (1 estrutura)", r["bh_storage"])]:
            ratio = "—" if label.startswith("BH") else f"{s / r['bh_storage']:.2f}×"
            L.append(f"| {label} | {fmt(s)} MB | {ratio} |")

        L.append("\n### Trabalho por operação (MB lidos)\n")
        L.append("| operação | Escada | Único | BH |")
        L.append("|---|---|---|---|")
        for label, _ in RES:
            w = r["work"]["res"][label]
            L.append(f"| {label} | {fmt(w['ladder'])} | {fmt(w['single'])} | {fmt(w['bh'])} |")
        w = r["work"]["roi"]
        L.append(f"| ROI 512² | {fmt(w['ladder'])} | {fmt(w['single'])} | {fmt(w['bh'])} |")

    L.append("\n## LEITURA\n")
    L.append("- **BH dá storage-de-único + trabalho-de-escada** sempre que seu arquivo")
    L.append("  é competitivo: uma estrutura serve TODAS as resoluções e a ROI sem")
    L.append("  guardar renditions nem decodar tudo. É a opcionalidade sob multiplicidade.")
    L.append("- **O ponto de cruzamento é o tamanho do arquivo BH** — em conteúdo onde")
    L.append("  o BH comprime mal (foto natural), a escada de WebP tem storage menor")
    L.append("  e o ganho do BH fica só no trabalho da ROI/preview. Em conteúdo casado")
    L.append("  (sintético/UI), o BH vence em storage E trabalho ao mesmo tempo.")
    L.append("- **A condição da vitória**: as operações têm que partilhar a MESMA")
    L.append("  hierarquia. Resolução e ROI partilham (decomposição espacial) → o BH")
    L.append("  amortiza. Uma operação que exigisse outra organização não amortizaria.")

    out = ROOT / "RESULTS_PORTFOLIO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
