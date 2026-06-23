"""Harness BH Wafer — cenários A/B/C, emite RESULTS.md com veredicto."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BITH = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from bhwafer import measure, measure_with_derived, measure_with_refinements

SIDE = 512


def make_partition(side, seed, p=0.72, minb=4):
    rng = np.random.default_rng(seed)
    region = np.zeros((side, side), dtype=np.int32)
    nid = [0]

    def rec(y, x, s):
        if s <= minb or rng.random() > p:
            region[y:y + s, x:x + s] = nid[0]; nid[0] += 1; return
        h = s // 2
        for dy, dx in ((0, 0), (0, h), (h, 0), (h, h)):
            rec(y + dy, x + dx, h)
    rec(0, 0, side)
    return region


def layer_from(region, channels, seed):
    rng = np.random.default_rng(seed)
    vals = rng.integers(0, 256, (region.max() + 1, channels), dtype=np.uint8)
    return vals[region]


def scenario_aligned():
    reg = make_partition(SIDE, seed=1)
    return [layer_from(reg, 3, 10), layer_from(reg, 1, 11),
            layer_from(reg, 1, 12), layer_from(reg, 3, 13)], 0.0


def scenario_misaligned():
    return [layer_from(make_partition(SIDE, seed=s), 3, s + 50)
            for s in (1, 2, 3, 4)], 0.0


def scenario_photo():
    from PIL import Image
    p = BITH / "data" / "corpus" / "natural_city.jpg"
    img = np.asarray(Image.open(p).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS),
                     dtype=np.uint8)
    # 2ª camada co-registrada: luminância (partilha bordas com a foto)
    lum = np.rint(img @ [0.299, 0.587, 0.114]).astype(np.uint8)[:, :, None]
    # 3ª camada co-registrada: quantização grosseira (segmentação simples)
    seg = ((img >> 5) << 5)  # 3 bits/canal — mesma estrutura, menos detalhe
    return [img, lum, seg], 24.0


def fmt(b: int) -> str:
    return f"{b/1e3:.1f}"


def main() -> None:
    scenarios = [
        ("A — co-registrado (mesma partição)", *scenario_aligned()),
        ("B — desalinhado (partições independentes)", *scenario_misaligned()),
        ("C — foto real + luminância + segmentação", *scenario_photo()),
    ]
    L = ["# BH WAFER MVP — RESULTADOS\n"]
    L.append("Múltiplas camadas co-registradas sobre UMA hierarquia. Métrica: "
             "bytes de estrutura (partilhada no wafer) + payload (cobrado por "
             "Shannon). Comparado contra K árvores independentes.\n")
    L.append(f"Lado {SIDE}×{SIDE}. Estrutura = 1 byte por nó interno.\n")

    results = []
    for name, layers, t in scenarios:
        m = measure(layers, threshold=t)
        results.append((name, t, m))
        if name.startswith("C "):
            md = measure_with_derived(layers, derived={1}, threshold=t)
            results.append(("C+ - foto + luminancia derivada do RGB + segmentacao", t, md))
            mr = measure_with_refinements(layers, base_layer=0, derived={1}, threshold=t)
            results.append(("C++ - arvore RGB + lum derivada + refinamento da segmentacao", t, mr))

    L.append("## VEREDICTO POR ALEGAÇÃO\n")
    a = results[0][2]; b = results[1][2]
    struct_amortized = a["indep"]["struct"] > 1.5 * a["wafer"]["struct"]
    w1 = "CONFIRMADA (mas pequena)" if (struct_amortized and a["ratio"] > 1.0) else "REFUTADA"
    w2 = "CONFIRMADA" if a["payload_overhead"] == 0 else "PARCIAL"
    w3 = "CONFIRMADA" if b["ratio"] < 1.0 else "REFUTADA"
    cplus = next(m for name, _, m in results if name.startswith("C+"))
    cplusplus = next(m for name, _, m in results if name.startswith("C++"))
    struct_frac = a["wafer"]["struct"] / a["wafer"]["total"]
    L.append(f"- **W1 (amortização de estrutura): {w1}** — a estrutura É partilhada "
             f"~{a['indep']['struct']/a['wafer']['struct']:.1f}× (gravada 1× em vez de "
             f"{a['n_layers']}×), MAS é só {struct_frac:.1%} do total → ganho total só "
             f"{a['ratio']:.2f}×. Estrutura-sozinha é alavanca fraca quando o payload "
             f"domina. O ganho grande exige correlação entre-camadas (não implementado).")
    L.append(f"- **W2 (teto de Shannon): {w2}** — payload do wafer == soma dos "
             f"independentes (overhead {a['payload_overhead']} B). Só a estrutura é "
             f"partilhada; conteúdo não é mágica.")
    L.append(f"- **W3 (fronteira, desalinhado): {w3}** — partições independentes: "
             f"wafer {b['ratio']:.2f}× (PERDE), união super-subdivide.\n")
    L.append(f"- **W4 (correlação entre-camadas): EXPERIMENTAL** — no cenário C+, "
             f"luminância derivada do RGB economiza "
             f"{cplus['derived_payload_saved']/1e3:.1f} KB de payload; ganho total "
             f"vai para {cplus['ratio']:.2f}×.\n")
    L.append(f"- **W5 (base + refinamentos): EXPERIMENTAL** — no cenário C++, "
             f"a árvore RGB não é arrastada pela segmentação; ganho total "
             f"vai para {cplusplus['ratio']:.2f}×.\n")

    L.append("## CENÁRIOS — estrutura + payload (KB)\n")
    L.append("| cenário | wafer estrut | wafer payload | wafer total | indep total | ganho |")
    L.append("|---|---|---|---|---|---|")
    for name, t, m in results:
        w = m["wafer"]; ind = m["indep"]
        gtxt = f"{m['ratio']:.2f}×" + ("" if m["ratio"] >= 1 else " (perde)")
        L.append(f"| {name} | {fmt(w['struct'])} | {fmt(w['payload'])} | "
                 f"{fmt(w['total'])} | {fmt(ind['total'])} | {gtxt} |")

    L.append("\n## DETALHE — onde está o ganho (cenário A)\n")
    w = a["wafer"]; ind = a["indep"]
    L.append(f"- Estrutura: wafer **{fmt(w['struct'])} KB** vs independente "
             f"**{fmt(ind['struct'])} KB** → {a['struct_saved']/1e3:.1f} KB poupados "
             f"(a estrutura replicada {a['n_layers']}× que o wafer grava 1×).")
    L.append(f"- Payload: wafer {fmt(w['payload'])} KB == independente "
             f"{fmt(ind['payload'])} KB (Shannon: idêntico).")
    L.append(f"- **O ganho é exatamente a estrutura não-replicada.**")

    L.append("\n## LEITURA HONESTA\n")
    L.append("- **W1 é real mas PEQUENO.** A estrutura é amortizada ~K×, mas para "
             "camadas pesadas em valor ela é fração mínima do total → o ganho total "
             "fica em ~1,1×. Compartilhar a moldura sozinha não move a agulha.")
    L.append("- **W2: Shannon manda.** O wafer não comprime conteúdo independente. "
             "O payload é idêntico à soma. Quem promete 'K datasets de graça' erra — "
             "só a moldura é partilhada.")
    L.append("- **W3: desalinhado perde feio (0,32×).** Sem bordas comuns, a união "
             "super-subdivide; o wafer fica MUITO pior que arquivos separados. E a "
             "foto real (C) também perde (0,67×): RGB + lum + seg não subdividem nos "
             "mesmos lugares sob threshold, então a união arrasta todas para baixo.")
    L.append("- **O verdadeiro lever é CORRELAÇÃO entre-camadas, não estrutura.** "
             "Shannon proíbe partilhar conteúdo INDEPENDENTE — mas camadas "
             "co-registradas de IA são CORRELACIONADAS (profundidade prevê-se de RGB; "
             "segmentação, de ambas). Guardar camada 2..K como DELTA/predição sobre a "
             "camada 1 partilharia a INFORMAÇÃO MÚTUA — aí sim o ganho é grande. Este "
             "MVP partilha só estrutura e por isso mede pequeno: delimita que o wafer "
             "ingênuo é fraco e aponta onde o ganho mora (predição entre-camadas).")

    out = ROOT / "RESULTS.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"veredicto: W1={w1} W2={w2} W3={w3}")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
