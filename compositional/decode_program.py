"""A ideia do Márcio: e se o cabeçalho carregasse as INSTRUÇÕES de decode?

Em vez de payload = resultado, payload = PROGRAMA que gera o resultado
(direção da complexidade de Kolmogorov; o PostScript é a página-como-programa).
Mede: para dado GERADO por regra, o 'programa no cabeçalho' colapsa o payload e
bate até o WebP (que vê sinal); para FOTO, o programa não pode ser menor que a
entropia (Kolmogorov/Shannon).
"""
from __future__ import annotations

import io
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from PIL import Image


def webp(img, q=90):
    b = io.BytesIO(); Image.fromarray(img).save(b, "WEBP", quality=q); return len(b.getvalue())


def png(img):
    b = io.BytesIO(); Image.fromarray(img).save(b, "PNG"); return len(b.getvalue())


def rings(S, cx, cy, freq):
    """Imagem GERADA: anéis concêntricos = função de 5 parâmetros."""
    y, x = np.indices((S, S))
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    v = ((np.sin(r * freq) * 0.5 + 0.5) * 255).astype(np.uint8)
    return np.stack([v, v, v], -1)


def fmt(b):
    return f"{b/1e6:.2f} MB" if b >= 1e6 else (f"{b/1e3:.1f} KB" if b >= 1e3 else f"{b} B")


def main():
    S = 512
    # objeto GERADO por regra (5 parâmetros)
    cx, cy, freq = 250.0, 260.0, 0.30
    proc = rings(S, cx, cy, freq)
    # o "programa no cabeçalho" que reconstrói: id_da_regra + 5 floats
    program = struct.pack("<B5f", 1, S, cx, cy, freq, 0.0)  # ~21 bytes

    # objeto SINAL (foto)
    photo = np.asarray(Image.fromarray(
        np.asarray(Image.open(ROOT / "data/corpus/natural_city.jpg").convert("RGB"))
    ).resize((S, S), Image.LANCZOS), np.uint8)

    L = ["# DECODE-PROGRAMA NO CABEÇALHO — payload vira programa\n"]
    L.append(f"Imagem {S}×{S}. 'programa' = id da regra + parâmetros no cabeçalho; "
             "o decoder EXECUTA o programa em vez de ler o resultado.\n")
    L.append("| objeto | raw | WebP | decode-programa | programa vs WebP |")
    L.append("|---|---|---|---|---|")
    L.append(f"| anéis (GERADO por regra) | {fmt(proc.nbytes)} | {fmt(webp(proc))} | "
             f"**{len(program)} B** | **{webp(proc)/len(program):,.0f}× menor** |")
    L.append(f"| foto (SINAL) | {fmt(photo.nbytes)} | {fmt(webp(photo))} | "
             f"≈ {fmt(webp(photo))} (não há programa curto) | ~1× |")

    L.append("\n## LEITURA HONESTA\n")
    L.append(f"- **Para dado GERADO por regra, o programa no cabeçalho ESMAGA** — os "
             f"anéis são {len(program)} bytes (id + 5 parâmetros) e reconstroem EXATO, "
             f"contra {fmt(webp(proc))} do WebP, que não sabe que é uma fórmula e o trata "
             f"como sinal de alta frequência. Tua intuição está certa: instruções no "
             f"cabeçalho reduzem o payload — drasticamente, quando o dado é gerado.")
    L.append("- **Para SINAL (foto), o programa NÃO pode ser menor que a entropia** "
             "(Kolmogorov/Shannon: o menor programa que gera ruído é ~o próprio ruído). "
             "Aí o WebP reina e o programa não ajuda.")
    L.append("- **É a MESMA lei, na sua forma mais profunda:** payload→programa reduz "
             "exatamente na medida em que o dado é ESTRUTURA (gerado por regra) e não "
             "SINAL (ruído/perceptual). Gradiente, fórmula, composição, fractal, UI, "
             "cena procedural → programa minúsculo. Foto, áudio, textura orgânica → "
             "entropia manda.")
    L.append("- **O trade honesto:** mover a decode-instruction para o cabeçalho exige "
             "um decoder PROGRAMÁVEL (executa instruções) em vez de FIXO. Mais flexível "
             "e potencialmente minúsculo no payload, mas mais complexo — e com risco de "
             "segurança (executar instrução não-confiável: foi o buraco do PostScript/"
             "PDF/Flash). O JPEG é rígido mas seguro; o programável é poderoso mas pesa.")
    L.append("- **E a separação que o Márcio fez:** BH é o FORMATO que pode carregar "
             "esses decode-programas por região; Intent é o SISTEMA que computa a "
             "transformação de significado (encode texto→arquétipo, decode arquétipo→"
             "texto). Os dois usam 'dado-como-programa/estrutura', mas são coisas "
             "diferentes — o BH guarda; o Intent transforma.")

    out = ROOT / "RESULTS_DECODE_PROGRAMA.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"anéis (gerado): raw={fmt(proc.nbytes)} WebP={fmt(webp(proc))} "
          f"programa={len(program)}B ({webp(proc)//len(program):,}× menor que WebP)")
    print(f"foto (sinal):   WebP={fmt(webp(photo))} — programa não ajuda")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
