"""Harness F4 — matriz imagem×modo, métricas da spec §7, veredicto §1.

Gera RESULTS.md. Critérios de veredicto (declarados, não ajustados depois):

C1 CONFIRMADA se: (a) no caso de árvore densa (ruído), fração lida ≤ 1.2×
   a fração geométrica em todos os níveis-alvo; E (b) em TODAS as imagens,
   ler o preview custa menos que armazenar uma rendition raw daquela
   resolução. PARCIAL se só (b). REFUTADA se nem (b).
C2 CONFIRMADA se payload lido ≤ 1.2× a fração de área em todas as
   imagens e regiões.
C3 (spec §1): natural lossless ≤ 2× PNG; sintético/screenshot ≤ PNG.
   Veredicto por classe.
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from PIL import Image, ImageDraw

from bench import corpus
from bhc import decode_full, decode_progressive, decode_roi, encode
from bhc.metrics import psnr

W, H = 3840, 2160
LOSSY_THRESHOLDS = [8.0, 24.0, 64.0]
ROI_FRACTIONS = [0.01, 0.0625, 0.25]
JPEG_QUALITIES = list(range(10, 96, 5))


def ui_screenshot(w: int, h: int) -> np.ndarray:
    """Screenshot sintético: barras, painéis e linhas de texto."""
    im = Image.new("RGB", (w, h), (246, 247, 249))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 120], fill=(36, 41, 56))
    d.rectangle([0, 120, 420, h], fill=(228, 231, 236))
    for i in range(28):
        y = 180 + i * 64
        d.rectangle([40, y, 380, y + 28], fill=(180, 186, 196))
    for col in range(2):
        x0 = 480 + col * 1680
        for row in range(12):
            y0 = 180 + row * 160
            d.rectangle([x0, y0, x0 + 1560, y0 + 130], fill=(255, 255, 255),
                        outline=(210, 214, 220), width=2)
            for line in range(3):
                ly = y0 + 20 + line * 34
                d.rectangle([x0 + 24, ly, x0 + 24 + 1100 - line * 260, ly + 16],
                            fill=(120, 128, 142))
    d.rectangle([w - 360, 20, w - 60, 100], fill=(58, 130, 246))
    return np.asarray(im, dtype=np.uint8)


def gather_corpus() -> list[tuple[str, str, np.ndarray]]:
    items = [
        ("sintetico", "flat", corpus.flat(W, H)),
        ("sintetico", "gradient", corpus.gradient(W, H)),
        ("sintetico", "shapes", corpus.shapes(W, H)),
        ("sintetico", "noise", corpus.noise(W, H)),
        ("screenshot", "ui", ui_screenshot(W, H)),
    ]
    natural_dir = ROOT / "data" / "corpus"
    photos = sorted(natural_dir.glob("natural_*.jpg"))
    for p in photos:
        items.append(("natural", p.stem, corpus.load_image(str(p))))
    if not photos:
        print("AVISO: sem fotos reais em data/corpus — usando proxy sintético")
        items.append(("natural", "natural_proxy", corpus.natural_proxy(W, H)))
    return items


def png_size(img: np.ndarray) -> int:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")  # compress_level default 6
    return buf.tell()


def jpeg_sweep(img: np.ndarray) -> list[tuple[int, int, float]]:
    pil = Image.fromarray(img)
    out = []
    for q in JPEG_QUALITIES:
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=q)
        dec = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
        out.append((q, buf.tell(), psnr(img, dec)))
    return out


def closest_jpeg(sweep, target_psnr):
    return min(sweep, key=lambda t: abs(t[2] - target_psnr))


def bench_image(cls: str, name: str, img: np.ndarray) -> dict:
    t0 = time.perf_counter()
    raw = img.nbytes
    blob_pyr, stats = encode(img, pyramid=True)
    blob_nopyr, _ = encode(img, pyramid=False)
    out, _ = decode_full(blob_pyr)
    assert np.array_equal(out, img), f"roundtrip falhou em {name}"
    png = png_size(img)
    n = stats["levels"]

    # C1: níveis-alvo relativos ao topo
    c1 = []
    for label, k in [("thumb", n - 4), ("480p", n - 3), ("1080p", n - 1)]:
        _, info = decode_progressive(blob_pyr, max_level=k)
        scale = 2 ** (n - k)
        rend_raw = -(-img.shape[1] // scale) * -(-img.shape[0] // scale) * 3
        geometric = (4.0**k / 4.0**n) * (4.0 / 3.0)
        c1.append({
            "label": label, "level": k,
            "bytes": info["bytes_read"], "fraction": info["fraction"],
            "geometric": geometric, "rendition_raw": rend_raw,
        })

    # C2: regiões centradas por fração de área
    c2 = []
    for f in ROI_FRACTIONS:
        rw, rh = int(W * f**0.5), int(H * f**0.5)
        x, y = (W - rw) // 2, (H - rh) // 2
        _, info = decode_roi(blob_pyr, x, y, rw, rh)
        c2.append({
            "area": info["roi_area_fraction"],
            "payload_fraction": info["payload_fraction"],
            "total_fraction": info["fraction"],
            "seeks": info["seeks"],
        })

    # C3 lossy: BH por threshold vs JPEG a PSNR equivalente
    lossy = []
    sweep = jpeg_sweep(img)
    for t in LOSSY_THRESHOLDS:
        b, _ = encode(img, lossy=True, threshold=t, pyramid=False)
        o, _ = decode_full(b)
        p = psnr(img, o)
        jq, jsize, jpsnr = closest_jpeg(sweep, p)
        lossy.append({
            "threshold": t, "size": len(b), "psnr": p,
            "jpeg_q": jq, "jpeg_size": jsize, "jpeg_psnr": jpsnr,
        })

    return {
        "class": cls, "name": name, "raw": raw, "png": png,
        "bh_lossless": len(blob_nopyr), "bh_pyramid": len(blob_pyr),
        "pyramid_overhead": (len(blob_pyr) - len(blob_nopyr)) / len(blob_nopyr),
        "levels": n, "leaves": stats["total_leaves"],
        "c1": c1, "c2": c2, "lossy": lossy,
        "bench_seconds": time.perf_counter() - t0,
    }


def verdicts(results: list[dict]) -> dict:
    # C1 (a): caso denso = ruído
    dense = next(r for r in results if r["name"] == "noise")
    c1_dense_ok = all(p["fraction"] <= 1.2 * p["geometric"] for p in dense["c1"])
    c1_rendition_ok = all(
        p["bytes"] < p["rendition_raw"] for r in results for p in r["c1"]
    )
    c1 = "CONFIRMADA" if (c1_dense_ok and c1_rendition_ok) else (
        "PARCIAL" if c1_rendition_ok else "REFUTADA")

    c2_ok = all(
        p["payload_fraction"] <= 1.2 * p["area"] for r in results for p in r["c2"]
    )
    c2 = "CONFIRMADA" if c2_ok else "REFUTADA"

    c3_parts = {}
    for cls, limit in [("sintetico", 1.0), ("screenshot", 1.0), ("natural", 2.0)]:
        rs = [r for r in results if r["class"] == cls and r["name"] != "noise"]
        if not rs:
            continue
        ok = all(r["bh_lossless"] <= limit * r["png"] for r in rs)
        c3_parts[cls] = "OK" if ok else "FALHOU"
    c3 = "CONFIRMADA" if all(v == "OK" for v in c3_parts.values()) else (
        "PARCIAL" if any(v == "OK" for v in c3_parts.values()) else "REFUTADA")
    return {"C1": c1, "C2": c2, "C3": c3, "C3_partes": c3_parts,
            "C1_denso_geometrico": c1_dense_ok, "C1_vs_rendition": c1_rendition_ok}


def fmt_mb(b: int) -> str:
    return f"{b / 1e6:.3f}"


def emit_markdown(results: list[dict], v: dict) -> str:
    L = []
    L.append("# BH CODEC MVP — RESULTADOS (F4)\n")
    L.append("Gerado pelo harness (`src/bench/harness.py`). Critérios de veredicto")
    L.append("declarados no topo do harness ANTES da medição — spec §1 e §7.\n")
    L.append("## VEREDICTO POR ALEGAÇÃO\n")
    L.append(f"- **C1 (decode progressivo): {v['C1']}** — caso denso ≤1.2× geométrico: "
             f"{'sim' if v['C1_denso_geometrico'] else 'não'}; preview sempre mais barato "
             f"que rendition raw: {'sim' if v['C1_vs_rendition'] else 'não'}")
    L.append(f"- **C2 (ROI proporcional): {v['C2']}** — payload ≤1.2× área em todas as "
             "imagens e regiões")
    partes = ", ".join(f"{k}: {x}" for k, x in v["C3_partes"].items())
    L.append(f"- **C3 (compressão aceitável): {v['C3']}** — {partes} "
             "(limites: sintético/screenshot ≤ PNG; natural ≤ 2× PNG; "
             "ruído excluído por ser adversarial declarado, spec §10 R1)\n")

    L.append("## TAMANHOS LOSSLESS (MB)\n")
    L.append("| classe | imagem | raw | PNG | BH s/ pirâmide | BH c/ pirâmide | BH/PNG | overhead pirâmide |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in results:
        L.append(
            f"| {r['class']} | {r['name']} | {fmt_mb(r['raw'])} | {fmt_mb(r['png'])} "
            f"| {fmt_mb(r['bh_lossless'])} | {fmt_mb(r['bh_pyramid'])} "
            f"| {r['bh_lossless'] / r['png']:.2f}× | {r['pyramid_overhead']:.1%} |")

    L.append("\n## C1 — CURVA PROGRESSIVA (bytes lidos por resolução)\n")
    L.append("| imagem | alvo | bytes (MB) | fração arquivo | fração geométrica | rendition raw (MB) |")
    L.append("|---|---|---|---|---|---|")
    for r in results:
        for p in r["c1"]:
            L.append(
                f"| {r['name']} | {p['label']} | {fmt_mb(p['bytes'])} "
                f"| {p['fraction']:.2%} | {p['geometric']:.2%} | {fmt_mb(p['rendition_raw'])} |")

    L.append("\n## C2 — ROI (custo por área)\n")
    L.append("| imagem | área | payload lido | total lido | seeks |")
    L.append("|---|---|---|---|---|")
    for r in results:
        for p in r["c2"]:
            L.append(f"| {r['name']} | {p['area']:.2%} | {p['payload_fraction']:.2%} "
                     f"| {p['total_fraction']:.2%} | {p['seeks']:,} |")

    L.append("\n## C3 LOSSY — BH vs JPEG a PSNR equivalente\n")
    L.append("| imagem | threshold | BH (MB) | PSNR BH | JPEG q | JPEG (MB) | PSNR JPEG | BH/JPEG |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in results:
        for p in r["lossy"]:
            ps = "inf" if p["psnr"] == float("inf") else f"{p['psnr']:.1f}"
            L.append(
                f"| {r['name']} | {p['threshold']:.0f} | {fmt_mb(p['size'])} | {ps} "
                f"| {p['jpeg_q']} | {fmt_mb(p['jpeg_size'])} | {p['jpeg_psnr']:.1f} "
                f"| {p['size'] / p['jpeg_size']:.1f}× |")

    L.append("\n## NOTAS DE HONESTIDADE\n")
    L.append("- Fotos naturais vêm de JPEG decodificado (Lorem Picsum/Unsplash): o ruído")
    L.append("  de bloco do JPEG degrada a quadtree lossless — o cenário real seria RAW")
    L.append("  de sensor, provavelmente pior ainda (mais ruído). O número fica como está.")
    L.append("- `noise` está nas tabelas mas fora do veredicto C3: é o adversarial")
    L.append("  declarado (spec §10 R1) — custo acima do raw é o esperado e foi medido.")
    L.append("- ROI paga piso fixo de estrutura (~8% do arquivo) — candidato a índice de")
    L.append("  ranks na v1; ver coluna 'total lido' vs 'payload lido'.")
    L.append("- PSNR do lossy BH em threshold alto vem com artefactos de bloco visíveis")
    L.append("  (spec §10 R3): PSNR não captura qualidade perceptual.")
    return "\n".join(L) + "\n"


def main() -> None:
    results = []
    for cls, name, img in gather_corpus():
        print(f"benchmarking {cls}/{name} ...", flush=True)
        results.append(bench_image(cls, name, img))
        print(f"  done in {results[-1]['bench_seconds']:.1f}s", flush=True)
    v = verdicts(results)
    md = emit_markdown(results, v)
    out = ROOT / "RESULTS.md"
    out.write_text(md, encoding="utf-8")
    print(f"\nveredicto: C1={v['C1']} C2={v['C2']} C3={v['C3']}")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
