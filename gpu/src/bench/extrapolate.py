"""Extrapolação honesta para GPUs superiores — a partir da banda de memória.

NÃO é medição: é aritmética sobre as bandas de memória publicadas. A tese a
testar: o ganho do BH ESCALA com a placa? Resposta — depende do regime.
  - lote bandwidth-bound (build domina): a RAZÃO é INVARIANTE de hardware.
  - consulta única latency-bound: a razão ENCOLHE em placas mais rápidas.
"""
from __future__ import annotations

# banda de memória publicada (GB/s)
GPUS = [
    ("RTX 3060 (medido aqui)", 360),
    ("RTX 4090", 1008),
    ("RTX 5090", 1792),
    ("A100 80GB", 2039),
    ("H100 SXM", 3350),
    ("H200", 4800),
    ("B200 (Blackwell)", 8000),
]

# carga do teste pesado
FLAT_TB = 3.51            # TB varridos pelo flat
BUILD_GB = 2.0            # GB lidos pelo build do agregado (1 passada no array)
LAUNCH_FLOOR_US = 2.8     # piso de lançamento de kernel (~const; medido na 3060)

# carga leve (1 consulta, redução total de 1 GB)
LIGHT_GB = 1.0


def s_from_gb(gb, bw_gbs):
    return gb / bw_gbs  # segundos


def main() -> None:
    print("=" * 78)
    print("LOTE PESADO (bandwidth-bound): flat 3,51 TB vs BH build 2 GB")
    print("=" * 78)
    print(f"{'GPU':<24}{'banda':>10}{'flat':>12}{'BH build':>12}{'razão':>10}")
    for name, bw in GPUS:
        flat_s = s_from_gb(FLAT_TB * 1000, bw)
        build_s = s_from_gb(BUILD_GB, bw)
        ratio = (FLAT_TB * 1000) / BUILD_GB  # invariante
        print(f"{name:<24}{bw:>8} GB/s{flat_s:>10.2f} s{build_s*1e3:>10.1f} ms{ratio:>9,.0f}×")
    print("-> a RAZÃO (~1.755×) é INVARIANTE: ambos escalam com a banda.")
    print("  placa melhor = mesmo ganho relativo, só mais rápido em absoluto.\n")

    print("=" * 78)
    print("CONSULTA ÚNICA (latency-bound): flat lê 1 GB vs BH no piso de lançamento")
    print("=" * 78)
    print(f"{'GPU':<24}{'banda':>10}{'flat':>11}{'razão SW':>10}{'razão NATIVO':>14}")
    NATIVE_FLOOR_US = 0.3  # HIPOTÉTICO: latência de memória, não lançamento de kernel
    for name, bw in GPUS:
        flat_us = s_from_gb(LIGHT_GB, bw) * 1e6
        ratio_sw = flat_us / LAUNCH_FLOOR_US        # BH emulado (piso = lançamento)
        ratio_native = flat_us / NATIVE_FLOOR_US    # BH no driver (piso = latência mem)
        print(f"{name:<24}{bw:>8} GB/s{flat_us:>8.0f} µs{ratio_sw:>8,.0f}×{ratio_native:>12,.0f}×")
    print(f"-> 'razão SW' = BH emulado (piso lançamento {LAUNCH_FLOOR_US} µs): ENCOLHE.")
    print(f"-> 'razão NATIVO' = BH no driver (piso latência mem {NATIVE_FLOOR_US} µs,")
    print(f"   HIPOTÉTICO): recupera ~{LAUNCH_FLOOR_US/NATIVE_FLOOR_US:.0f}× porque o piso")
    print("   deixa de ser o lançamento de kernel. O floor é SOFTWARE, não física.\n")


if __name__ == "__main__":
    main()
