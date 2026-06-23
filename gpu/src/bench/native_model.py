"""Modelo paramétrico para HARDWARE NATIVO — projeção, não medição.

Cada parâmetro tem PROVENIÊNCIA explícita:
  [MEDIDO]      vem dos nossos testes reais na RTX 3060
  [PROJETADO]   número físico/publicado (com a fonte) — não medido por nós
  [ESPECULATIVO] propriedade de silício BH-nativo que não existe

O modelo dá PROJEÇÕES. O valor é a transparência: troque um parâmetro e veja
o resultado mudar. Nada aqui é "×speedup de hardware medido".
"""
from __future__ import annotations

# ----------------------- PARÂMETROS -----------------------
# [MEDIDO] RTX 3060, nossos testes (real_gpu.py / heavy_gpu.py)
BW_EFF = 342e9          # B/s — banda efetiva ótima medida (cupy reduction)
LAUNCH_FLOOR = 2.8e-6   # s — piso de lançamento de kernel medido (BH O(1))
BUILD_READS_ARRAY = True  # build lê o array 1× (bandwidth-bound) — medido

# [PROJETADO] números físicos/publicados (NÃO medidos por nós)
MEM_LATENCY = 0.3e-6    # s — latência de acesso GDDR6 (~300 ns, publicado).
                        #     seria o piso de um BH NATIVO (ler agregado, não lançar kernel)
ENERGY_PER_BYTE = 5e-12  # J/B — energia p/ mover 1 byte de DRAM (~ordem publicada;
                         #     PARÂMETRO incerto — varie e veja a sensibilidade)

# [ESPECULATIVO] o que o silício BH-nativo poderia fazer
NEAR_MEMORY_BUILD = True  # se o controlador computa agregados durante a escrita,
                          # o build "some" (amortizado na ingestão dos dados)

# Cenários (do teste pesado real)
SINGLE_GB = 1.0          # consulta única: redução de 1 GB
BATCH_FLAT_TB = 3.51     # lote: tráfego flat
BATCH_BUILD_GB = 2.0     # build do agregado (lê o array 1×)
BATCH_QUERIES = 6000


def s(x): return x


def fmt_t(t):
    if t >= 1: return f"{t:.2f} s"
    if t >= 1e-3: return f"{t*1e3:.2f} ms"
    return f"{t*1e6:.2f} µs"


def main() -> None:
    print("=" * 76)
    print("MODELO HARDWARE NATIVO — projeção a partir dos testes reais (RTX 3060)")
    print("=" * 76)
    print("[MEDIDO] BW=342 GB/s, piso lançamento=2.8µs | [PROJETADO] latência mem=0.3µs,")
    print("energia=5 pJ/B | [ESPECULATIVO] build near-memory\n")

    # ---- 1. LATÊNCIA consulta única ----
    t_flat = SINGLE_GB * 1e9 / BW_EFF
    t_sw = LAUNCH_FLOOR
    t_native = MEM_LATENCY
    print("1) LATÊNCIA — consulta única (redução de 1 GB)")
    print(f"   flat (varre 1 GB) ........ {fmt_t(t_flat):>9}   [MEDIDO]")
    print(f"   BH software (piso kernel)  {fmt_t(t_sw):>9}   [MEDIDO]  -> {t_flat/t_sw:,.0f}×")
    print(f"   BH NATIVO (latência mem) .. {fmt_t(t_native):>9}   [PROJETADO] -> {t_flat/t_native:,.0f}×")
    print(f"   ganho do nativo sobre o software: {t_sw/t_native:.0f}× (o piso deixa de ser o lançamento)\n")

    # ---- 2. LOTE (tempo) ----
    t_flat_b = BATCH_FLAT_TB * 1e12 / BW_EFF
    build_t = (BATCH_BUILD_GB * 1e9 / BW_EFF) if BUILD_READS_ARRAY else 0.0
    # software: build (bandwidth-bound) + consultas vetorizadas (~1 lançamento)
    t_bh_sw = build_t + LAUNCH_FLOOR
    # nativo: build folded? + N consultas a latência de memória
    build_native = 0.0 if NEAR_MEMORY_BUILD else build_t
    t_bh_native = build_native + BATCH_QUERIES * MEM_LATENCY
    print("2) LOTE — 6.000 consultas de agregação (flat varre 3,51 TB)")
    print(f"   flat ..................... {fmt_t(t_flat_b):>9}   [MEDIDO base]")
    print(f"   BH software (build+gather) {fmt_t(t_bh_sw):>9}   -> {t_flat_b/t_bh_sw:,.0f}×")
    print(f"   BH NATIVO (build folded) .. {fmt_t(t_bh_native):>9}   [PROJ+ESPEC] -> {t_flat_b/t_bh_native:,.0f}×")
    print(f"   nota: o build ({fmt_t(build_t)}) é o custo dominante do BH; se o controlador")
    print(f"   o calcula na escrita (near-memory), ele some.\n")

    # ---- 3. ENERGIA ----
    e_flat = BATCH_FLAT_TB * 1e12 * ENERGY_PER_BYTE
    e_bh = BATCH_BUILD_GB * 1e9 * ENERGY_PER_BYTE
    print("3) ENERGIA — proporcional aos dados movidos (prop. a bytes)")
    print(f"   flat move 3,51 TB ........ {e_flat:8.2f} J   [MEDIDO bytes × PROJ energia]")
    print(f"   BH move ~2 GB (build) .... {e_bh*1e3:8.2f} mJ  -> {e_flat/e_bh:,.0f}× menos energia")
    print(f"   (prop. a dados movidos = mesma razão ~1.755× do tempo bandwidth-bound)\n")

    print("=" * 76)
    print("LIMITES DO MODELO (o que ele NÃO captura)")
    print("=" * 76)
    for line in [
        "- design real de silício, área, custo de fabricação (anos, foundry).",
        "- overhead do compute near-memory (assumido ~0; real > 0).",
        "- a energia/byte é ordem de grandeza publicada, não medida aqui — varie-a.",
        "- a latência nativa de 0.3µs é a latência de memória, não medição de um",
        "  primitivo BH (que não existe). É o PISO físico, um teto otimista.",
        "- Amdahl ainda governa o nível da aplicação (ganho_app = 1/(1-f)).",
    ]:
        print(line)

    # ---- emite o artefacto markdown ----
    L = ["# BH — PROJEÇÃO PARA HARDWARE NATIVO\n"]
    L.append("Projeção a partir dos testes reais na RTX 3060. **Não é medição de "
             "hardware nativo** (que não existe). Proveniência por linha: "
             "[MEDIDO] = nossos testes · [PROJETADO] = físico/publicado · "
             "[ESPECULATIVO] = silício BH-nativo.\n")
    L.append("Parâmetros: BW=342 GB/s [MEDIDO] · piso lançamento=2,8 µs [MEDIDO] · "
             "latência memória=0,3 µs [PROJETADO] · energia=5 pJ/B [PROJETADO] · "
             "build near-memory [ESPECULATIVO].\n")
    L.append("## Projeções\n")
    L.append("| cenário | flat | BH software | ganho SW | BH nativo | ganho NATIVO |")
    L.append("|---|---|---|---|---|---|")
    L.append(f"| latência consulta única (1 GB) | {fmt_t(t_flat)} | {fmt_t(t_sw)} | "
             f"{t_flat/t_sw:,.0f}× | {fmt_t(t_native)} | **{t_flat/t_native:,.0f}×** |")
    L.append(f"| lote 6.000 consultas (3,51 TB) | {fmt_t(t_flat_b)} | {fmt_t(t_bh_sw)} | "
             f"{t_flat_b/t_bh_sw:,.0f}× | {fmt_t(t_bh_native)} | **{t_flat_b/t_bh_native:,.0f}×** |")
    L.append(f"| energia (lote) | {e_flat:.1f} J | — | — | {e_bh*1e3:.1f} mJ | "
             f"**{e_flat/e_bh:,.0f}× menos** |")
    L.append("\n## Leitura honesta\n")
    L.append("- **Latência nativa recupera ~9×** sobre o software: o piso troca de "
             "lançamento de kernel (2,8 µs, artefacto de software) para latência de "
             "memória (0,3 µs, física). [PROJETADO]")
    L.append("- **Lote nativo (~5.700×)** assume build folded near-memory "
             "[ESPECULATIVO]; sem isso, fica no ~1.755× do software.")
    L.append("- **Energia (~1.755× menos) é a parte robusta**: a razão depende só do "
             "quociente de bytes movidos [MEDIDO]; o valor absoluto em Joules é que "
             "depende do pJ/B [PROJETADO].")
    L.append("- **Amdahl** governa a app: ganho de operação S vira 1/((1-f)+f/S) na "
             "aplicação. Nada aqui é speedup de app.")
    L.append("- **NUNCA reportar como medição.** Toda linha é projeção até existir "
             "silício. Spec: `BH_NATIVE_HARDWARE_MODEL_SPEC.md`.")
    out = __import__("pathlib").Path(__file__).resolve().parents[2] / "RESULTS_NATIVE_PROJECTION.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nartefacto: {out}")


if __name__ == "__main__":
    main()
