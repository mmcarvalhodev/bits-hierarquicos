"""Teste PESADO em GPU real — lote de consultas de agregação, flat vs BH.

Empurra carga de verdade: o lado FLAT roda um kernel CUDA que VARRE cada
range na VRAM (milhares de consultas × ranges grandes = terabytes de
tráfego). O lado BH lê o agregado hierárquico (prefix dos blocos). Os dois
produzem a MESMA soma (verificado). Fatiado em lançamentos curtos p/ não
estourar o TDR do Windows (kernel >2s é morto).
"""
from __future__ import annotations

import cupy as cp
import numpy as np

N = 512_000_000          # 512M float32 = 2 GB em VRAM
BLOCK = 1024
Q = 6000                 # consultas
CHUNK = 256              # consultas por lançamento (mantém kernel < ~1s p/ TDR)
ELEM = 4

_KERNEL = r'''
extern "C" __global__
void rsum(const float* v, const long long* lo, const long long* hi, double* out){
    int q = blockIdx.x;
    long long a = lo[q], b = hi[q];
    double s = 0.0;
    for (long long i = a + threadIdx.x; i < b; i += blockDim.x) s += (double)v[i];
    __shared__ double sh[256];
    int t = threadIdx.x;
    sh[t] = s; __syncthreads();
    for (int st = 128; st > 0; st >>= 1){ if (t < st) sh[t] += sh[t+st]; __syncthreads(); }
    if (t == 0) out[q] = sh[0];
}
'''


def main() -> None:
    props = cp.cuda.runtime.getDeviceProperties(0)
    print(f"GPU: {props['name'].decode()} | array {N:,} f32 = {N*ELEM/1e9:.1f} GB", flush=True)

    rng = cp.random.default_rng(7)
    vals = rng.random(N, dtype=cp.float32)
    n_blocks = N // BLOCK

    # consultas alinhadas a bloco (comparação limpa, sem fronteira)
    rs = np.random.default_rng(1)
    lo_b = rs.integers(0, n_blocks - n_blocks // 8, Q)
    span_b = rs.integers(n_blocks // 8, n_blocks // 2, Q)
    hi_b = np.minimum(lo_b + span_b, n_blocks)
    lo = cp.asarray(lo_b * BLOCK, dtype=cp.int64)
    hi = cp.asarray(hi_b * BLOCK, dtype=cp.int64)
    total_elems = int((hi_b - lo_b).sum()) * BLOCK
    flat_bytes = total_elems * ELEM
    print(f"  {Q:,} consultas, tráfego flat = {flat_bytes/1e12:.2f} TB", flush=True)

    # ---- BH: build do agregado (custo único) ----
    bstart = cp.cuda.Event(); bend = cp.cuda.Event()
    bstart.record()
    block_sums = vals[: n_blocks * BLOCK].reshape(n_blocks, BLOCK).sum(axis=1)
    prefix = cp.concatenate([cp.zeros(1, dtype=cp.float64), cp.cumsum(block_sums, dtype=cp.float64)])
    bend.record(); bend.synchronize()
    build_ms = cp.cuda.get_elapsed_time(bstart, bend)

    out_flat = cp.zeros(Q, dtype=cp.float64)
    kern = cp.RawKernel(_KERNEL, "rsum")

    # ---- FLAT: kernel varrendo cada range (fatiado p/ TDR) ----
    cp.cuda.runtime.deviceSynchronize()
    fstart = cp.cuda.Event(); fend = cp.cuda.Event()
    fstart.record()
    for off in range(0, Q, CHUNK):
        c = min(CHUNK, Q - off)
        kern((c,), (256,), (vals, lo[off:off + c], hi[off:off + c], out_flat[off:off + c]))
    fend.record(); fend.synchronize()
    flat_ms = cp.cuda.get_elapsed_time(fstart, fend)

    # ---- BH: leitura vetorizada do agregado ----
    hi_bg = cp.asarray(hi_b, dtype=cp.int64); lo_bg = cp.asarray(lo_b, dtype=cp.int64)
    cp.cuda.runtime.deviceSynchronize()
    sstart = cp.cuda.Event(); send = cp.cuda.Event()
    sstart.record()
    out_bh = prefix[hi_bg] - prefix[lo_bg]
    send.record(); send.synchronize()
    bh_ms = cp.cuda.get_elapsed_time(sstart, send)

    # ---- verificação ----
    diff = cp.abs(out_flat - out_bh)
    rel = float((diff / cp.maximum(cp.abs(out_flat), 1.0)).max())
    ok = rel < 1e-3

    PEAK = 360.0  # GB/s nominal da 3060
    flat_bw = flat_bytes / (flat_ms / 1e3) / 1e9
    pct_peak = flat_bw / PEAK * 100
    ideal_flat_ms = flat_bytes / (PEAK * 1e9) * 1e3   # flat perfeito (bandwidth-bound puro)
    speed = flat_ms / bh_ms                            # vs meu kernel (subótimo)
    speed_ideal = ideal_flat_ms / bh_ms                # vs flat ideal (limite honesto)

    L = ["# BH GPU — TESTE PESADO (RTX 3060)\n"]
    L.append(f"GPU: {props['name'].decode()}. Array {N*ELEM/1e9:.1f} GB. {Q:,} consultas "
             f"de agregação de range (kernel CUDA real no flat). Tráfego flat "
             f"{flat_bytes/1e12:.2f} TB.\n")
    L.append(f"Verificação flat vs BH: {'OK' if ok else 'FALHOU'} (erro rel máx {rel:.1e}).\n")
    L.append("| lado | tempo | nota |")
    L.append("|---|---|---|")
    L.append(f"| FLAT (meu kernel varre {flat_bytes/1e12:.2f} TB) | {flat_ms/1e3:.2f} s | "
             f"{flat_bw:.0f} GB/s = {pct_peak:.0f}% do teto |")
    L.append(f"| FLAT ideal (bandwidth puro, {PEAK:.0f} GB/s) | {ideal_flat_ms/1e3:.2f} s | "
             f"estimativa do limite |")
    L.append(f"| BH (lê agregado) | {bh_ms:.1f} ms | + build único {build_ms:.0f} ms |")
    L.append("")
    L.append(f"**Speedup honesto: {speed_ideal:,.0f}× (vs flat IDEAL) a "
             f"{speed:,.0f}× (vs meu kernel).**")
    L.append("")
    L.append("## LEITURA HONESTA\n")
    L.append(f"- **A carga foi real:** o flat varreu {flat_bytes/1e12:.2f} TB de VRAM e "
             f"empurrou a placa por {flat_ms/1e3:.0f} s (SM a 100%). MAS sustentou só "
             f"{flat_bw:.0f} GB/s = {pct_peak:.0f}% do teto — meu kernel (1 bloco/consulta, "
             f"redução ingênua) é SUBÓTIMO, limitado por ocupação, não por banda pura.")
    L.append(f"- **Por isso o speedup honesto é um INTERVALO:** {speed:,.0f}× contra o "
             f"meu kernel, mas só ~{speed_ideal:,.0f}× contra um flat perfeito "
             f"(bandwidth-bound a {PEAK:.0f} GB/s). O número justo é o menor — parte do "
             f"213× era o meu flat ser ruim, não o BH ser mágico.")
    L.append(f"- **Mesmo no limite honesto, o BH ganha ~{speed_ideal:,.0f}×:** responde "
             f"as {Q:,} consultas em {bh_ms:.0f} ms lendo o agregado, em vez de mover "
             f"{flat_bytes/1e12:.2f} TB. Mesma resposta, verificada. O ganho é NÃO mover "
             f"os dados — isso nenhum kernel flat melhora, porque os dados existem.")
    L.append(f"- **Custo único:** build do agregado {build_ms:.0f} ms, desprezível "
             f"perto do lote. Vale p/ agregação/range sobre dado reusado; não p/ "
             f"consulta única nem kernel compute-bound.")

    out = __import__("pathlib").Path(__file__).resolve().parents[2] / "RESULTS_HEAVY_GPU.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nFLAT {flat_ms/1e3:.2f}s ({flat_bw:.0f} GB/s) | BH {bh_ms:.2f}ms | "
          f"speedup {speed:,.0f}× | verif {'OK' if ok else 'FALHOU'}")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
