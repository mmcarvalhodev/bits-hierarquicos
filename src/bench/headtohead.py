"""Head-to-head por TAREFA: BH vs codecs polidos (PNG, JPEG, WebP).

A pergunta não é "o BH comprime melhor?" (não comprime, em foto natural).
É: "para uma TAREFA REAL, quanto trabalho cada formato precisa?"

Tarefas:
  A — gerar um thumbnail (~256px) de um 4K armazenado
  B — extrair uma região 512×512 de um 4K armazenado
  C — armazenar conteúdo que casa com a interpretação (gradiente), lossy

Métrica primária: BYTES LIDOS do armazenamento para cumprir a tarefa
  (justa — independe de C vs Python). Um codec polido precisa do arquivo
  inteiro para thumbnail/ROI; o BH lê só o prefixo / o ramo.
Métrica secundária: tempo de parede (com ressalva: BH é Python puro,
  os outros são C otimizado — o tempo favorece os polidos por implementação,
  não por arquitetura).
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from PIL import Image

from bench import corpus
from bench.harness import ui_screenshot
from bhc import decode_progressive, decode_roi, encode
from bhc.metrics import psnr

W, H = 3840, 2160
THUMB = 256
ROI = (W // 2 - 256, H // 2 - 256, 512, 512)
N_TIMING = 3


def _time(fn) -> tuple[object, float]:
    best = float("inf")
    res = None
    for _ in range(N_TIMING):
        t0 = time.perf_counter()
        res = fn()
        dt = time.perf_counter() - t0
        best = min(best, dt)
    return res, best


def polished_stores(img: np.ndarray) -> dict:
    """Codifica a imagem nos codecs polidos. Retorna bytes de cada um."""
    pil = Image.fromarray(img)
    out = {}
    b = io.BytesIO(); pil.save(b, format="PNG"); out["PNG"] = b.getvalue()
    b = io.BytesIO(); pil.save(b, format="JPEG", quality=85); out["JPEG"] = b.getvalue()
    b = io.BytesIO(); pil.save(b, format="WEBP", quality=85); out["WebP"] = b.getvalue()
    return out


def task_thumbnail(img, bhc_blob, bhc_level, stores) -> list[dict]:
    rows = []

    def bh():
        prev, info = decode_progressive(bhc_blob, max_level=bhc_level)
        return info["bytes_read"]

    (bytes_read), t = _time(bh)
    rows.append({"fmt": "BH", "bytes_read": bytes_read, "time": t})

    for fmt, data in stores.items():
        def do(data=data):
            # codec polido: precisa do arquivo inteiro para abrir e reduzir
            im = Image.open(io.BytesIO(data))
            if fmt == "JPEG":
                im.draft("RGB", (THUMB, THUMB))  # dá ao JPEG seu fast-path
            im = im.convert("RGB")
            im.thumbnail((THUMB, THUMB))
            return len(data)
        br, t = _time(do)
        rows.append({"fmt": fmt, "bytes_read": br, "time": t})
    return rows


def task_roi(img, bhc_blob, stores) -> list[dict]:
    rows = []
    x, y, w, h = ROI

    def bh():
        _, info = decode_roi(bhc_blob, x, y, w, h)
        return info["bytes_read"]

    br, t = _time(bh)
    rows.append({"fmt": "BH", "bytes_read": br, "time": t})

    for fmt, data in stores.items():
        def do(data=data):
            im = Image.open(io.BytesIO(data)).convert("RGB")  # decodifica tudo
            _ = np.asarray(im)[y : y + h, x : x + w].copy()    # depois recorta
            return len(data)
        bytes_read, t = _time(do)
        rows.append({"fmt": fmt, "bytes_read": bytes_read, "time": t})
    return rows


def task_gradient_lossy() -> list[dict]:
    """Conteúdo que casa com a interpretação rampa: tamanho a PSNR alta."""
    img = corpus.gradient(W, H)
    rows = []
    blob, _ = encode(img, lossy=True, threshold=6.0, pyramid=False)
    out, _ = decode_progressive(blob, max_level=99)
    rows.append({"fmt": "BH-ramp", "size": len(blob), "psnr": psnr(img, out)})
    pil = Image.fromarray(img)
    for fmt, kw in [("JPEG", dict(quality=95)), ("WebP", dict(quality=95)),
                    ("PNG", {})]:
        b = io.BytesIO(); pil.save(b, format=fmt.replace("WebP", "WEBP"), **kw)
        dec = np.asarray(Image.open(io.BytesIO(b.getvalue())).convert("RGB"))
        rows.append({"fmt": fmt, "size": b.tell(), "psnr": psnr(img, dec)})
    return rows


def thumb_level(levels: int) -> int:
    """Nível cuja grade fica >= THUMB (preview na resolução do thumbnail)."""
    k = 0
    while 2**k < THUMB and k < levels:
        k += 1
    return min(k, levels)


def main() -> None:
    images = [
        ("gradient", corpus.gradient(W, H)),
        ("shapes", corpus.shapes(W, H)),
        ("ui", ui_screenshot(W, H)),
        ("natural_city", corpus.load_image(str(ROOT / "data/corpus/natural_city.jpg"))),
    ]
    lines = ["# HEAD-TO-HEAD POR TAREFA — BH vs codecs polidos\n"]
    lines.append("Métrica primária: **bytes lidos** para cumprir a tarefa "
                 "(justa, independe de linguagem).")
    lines.append("Tempo: BH é Python puro; PNG/JPEG/WebP são C otimizado — "
                 "o tempo favorece os polidos por implementação.\n")

    for name, img in images:
        print(f"processando {name} ...", flush=True)
        blob, stats = encode(img, lossy=True, threshold=6.0, pyramid=True)
        stores = polished_stores(img)
        lvl = thumb_level(stats["levels"])

        lines.append(f"\n## {name}  (BH {len(blob)/1e6:.2f} MB · "
                     f"PNG {len(stores['PNG'])/1e6:.2f} · "
                     f"JPEG {len(stores['JPEG'])/1e6:.2f} · "
                     f"WebP {len(stores['WebP'])/1e6:.2f})\n")

        ta = task_thumbnail(img, blob, lvl, stores)
        bh_a = next(r for r in ta if r["fmt"] == "BH")
        lines.append("### Tarefa A — thumbnail ~256px")
        lines.append("| formato | bytes lidos | vs BH | tempo (ms) |")
        lines.append("|---|---|---|---|")
        for r in ta:
            ratio = "—" if r["fmt"] == "BH" else f"{r['bytes_read']/bh_a['bytes_read']:.0f}× mais"
            lines.append(f"| {r['fmt']} | {r['bytes_read']/1e6:.3f} MB | {ratio} | {r['time']*1e3:.1f} |")

        tb = task_roi(img, blob, stores)
        bh_b = next(r for r in tb if r["fmt"] == "BH")
        lines.append("\n### Tarefa B — região central 512×512")
        lines.append("| formato | bytes lidos | vs BH | tempo (ms) |")
        lines.append("|---|---|---|---|")
        for r in tb:
            ratio = "—" if r["fmt"] == "BH" else f"{r['bytes_read']/bh_b['bytes_read']:.0f}× mais"
            lines.append(f"| {r['fmt']} | {r['bytes_read']/1e6:.3f} MB | {ratio} | {r['time']*1e3:.1f} |")

    lines.append("\n## Tarefa C — tamanho lossy em conteúdo que casa (gradiente)\n")
    lines.append("| formato | tamanho | PSNR (dB) |")
    lines.append("|---|---|---|")
    for r in task_gradient_lossy():
        lines.append(f"| {r['fmt']} | {r['size']/1e3:.1f} KB | {r['psnr']:.1f} |")

    lines.append("\n## LEITURA\n")
    lines.append("- **Acesso (A, B): o BH vence por construção** — codec polido precisa")
    lines.append("  do arquivo inteiro para thumbnail/ROI; o BH lê o prefixo / o ramo.")
    lines.append("  Polimento não muda isso: é estrutural.")
    lines.append("- **Compressão de foto natural: o polido vence** — e o relatório não")
    lines.append("  esconde (ver tamanhos no cabeçalho de natural_city).")
    lines.append("- **Conteúdo casado (C): a interpretação certa bate o polido** em")
    lines.append("  ordens de grandeza — a tese 'interpretação é a alavanca'.")

    out = ROOT / "RESULTS_HEADTOHEAD.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nrelatório: {out}")


if __name__ == "__main__":
    main()
