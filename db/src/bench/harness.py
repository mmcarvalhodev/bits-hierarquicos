"""Harness BH DB — roda Q1-Q4, emite RESULTS.md com veredicto por alegação.

Métrica primária: linhas lidas (BH vs baseline plano). Critérios declarados
ANTES da medição (spec §1 e §6).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from bhdb import AggregateTree, make_dataset
from bhdb import table as T

N = 1_000_000
BLOCK = 1024


def timed(fn, repeat=3):
    best = float("inf")
    out = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        out = fn()
        best = min(best, time.perf_counter() - t0)
    return out, best


def fmt(n: int) -> str:
    return f"{n:,}"


def main() -> None:
    print("gerando dataset 1M ...", flush=True)
    tbl = make_dataset(N, seed=7)
    print("construindo árvore (val_trend) ...", flush=True)
    tree = AggregateTree(tbl, col="val_trend", block=BLOCK)

    span = tbl.key[-1] - tbl.key[0]
    lo10 = int(tbl.key[0] + span * 0.2)
    hi10 = int(lo10 + span * 0.1)
    lo_narrow = int(tbl.key[0] + span * 0.4)
    hi_narrow = int(lo_narrow + span * 0.02)
    p99 = float(np.percentile(tbl.val_trend, 99))
    p99r = float(np.percentile(tbl.val_rand, 99))
    p50 = float(np.percentile(tbl.val_trend, 50))

    rows = []  # (id, desc, claim, bh_rows, base_rows, bh_t, base_t)

    # Q1 — agregado global (D1)
    (_, info), bt = timed(lambda: tree.aggregate_global())
    (_, binfo), bb = timed(lambda: T.full_scan_sum(tbl.val_trend))
    rows.append(("Q1", "SUM global", "D1", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q2 — agregado de range 10% (D1)
    (res, info), bt = timed(lambda: tree.aggregate_range(lo10, hi10))
    (_, binfo), bb = timed(lambda: T.range_scan_sum(tbl.key, tbl.val_trend, lo10, hi10))
    rows.append(("Q2", "SUM range 10%", "D1", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q3a — filtro no eixo (key) estreito (D2)
    (c, info), bt = timed(lambda: tree.prune_range_count(lo_narrow, hi_narrow))
    base = lambda: (int(((tbl.key >= lo_narrow) & (tbl.key <= hi_narrow)).sum()),
                    {"rows_read": len(tbl)})
    (_, binfo), bb = timed(base)
    rows.append(("Q3a", "COUNT key in 2%", "D2", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q3b — filtro correlacionado (val_trend > p99) (D2)
    (c, info), bt = timed(lambda: tree.prune_filter_count("gt", p99))
    (_, binfo), bb = timed(lambda: T.filter_scan_count(tbl.val_trend, "gt", p99))
    rows.append(("Q3b", "COUNT val_trend>p99", "D2", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q4a — filtro independente (val_rand > p99) (D3)
    (c, info), bt = timed(lambda: tree.prune_filter_count_col("val_rand", "gt", p99r))
    (_, binfo), bb = timed(lambda: T.filter_scan_count(tbl.val_rand, "gt", p99r))
    rows.append(("Q4a", "COUNT val_rand>p99", "D3", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q4b — filtro fora-de-eixo (region) (D3)
    (c, info), bt = timed(lambda: tree.off_axis_region_count(3))
    (_, binfo), bb = timed(lambda: T.filter_scan_eq_count(tbl.region, 3))
    rows.append(("Q4b", "COUNT region==3", "D3", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q5 -- mesma query com interpretacao categorica materializada (region_counts)
    (c, info), bt = timed(lambda: tree.region_count(3))
    (_, binfo), bb = timed(lambda: T.filter_scan_eq_count(tbl.region, 3))
    rows.append(("Q5", "COUNT region==3 (region_counts)", "D2+", info["rows_read"], binfo["rows_read"], bt, bb))

    # Q4c — filtro pouco seletivo (val_trend > mediana) (D3)
    (c, info), bt = timed(lambda: tree.prune_filter_count("gt", p50))
    (_, binfo), bb = timed(lambda: T.filter_scan_count(tbl.val_trend, "gt", p50))
    rows.append(("Q4c", "COUNT val_trend>p50", "D3", info["rows_read"], binfo["rows_read"], bt, bb))

    # veredicto
    def gain(bh, base):
        return base / bh if bh > 0 else float("inf")

    d1 = [r for r in rows if r[2] == "D1"]
    d2 = [r for r in rows if r[2] == "D2"]
    d1_ok = all(r[3] <= 2 * BLOCK for r in d1)
    d2_ok = all(gain(r[3], r[4]) >= 3.0 for r in d2)
    v1 = "CONFIRMADA" if d1_ok else "REFUTADA"
    v2 = "CONFIRMADA" if d2_ok else "PARCIAL"

    L = ["# BH DB MVP — RESULTADOS\n"]
    L.append(f"Dataset: {fmt(N)} linhas · bloco {fmt(BLOCK)} · árvore binária de agregação.")
    L.append("Métrica primária: **linhas lidas** (independe de linguagem). Tempo: "
             "NumPy nos dois lados; o full scan é vetorizado em C, então o tempo "
             "favorece o baseline — a métrica honesta é linhas lidas.\n")

    L.append("## VEREDICTO POR ALEGAÇÃO\n")
    L.append(f"- **D1 (agregação ≈ thumbnail): {v1}** — agregados lêem ≤ 2 blocos "
             f"de fronteira, nunca o range/tabela.")
    L.append(f"- **D2 (filtro seletivo ≈ ROI): {v2}** — poda no eixo organizado / "
             f"coluna correlacionada ganha ≥ 3× do full scan.")
    L.append(f"- **D3 (fronteira declarada): REPORTADA** — eixo não-agregado, valor "
             f"independente ou baixa seletividade → poda inútil, lê ~tudo. Esperado, "
             f"medido, não escondido.\n")

    L.append("## QUERIES — linhas lidas (BH vs plano)\n")
    L.append("| query | descrição | alegação | BH lê | plano lê | ganho | tempo BH/plano (ms) |")
    L.append("|---|---|---|---|---|---|---|")
    for qid, desc, claim, bh_r, base_r, bt, bb in rows:
        g = gain(bh_r, base_r)
        gtxt = "∞" if g == float("inf") else (f"{g:,.0f}×" if g >= 1 else f"{g:.2f}× (perde)")
        L.append(f"| {qid} | {desc} | {claim} | {fmt(bh_r)} | {fmt(base_r)} | {gtxt} "
                 f"| {bt*1e3:.1f} / {bb*1e3:.1f} |")

    L.append("\n## A MESMA ÁRVORE, QUATRO LEITURAS\n")
    L.append("Nenhum índice separado foi construído. A MESMA estrutura respondeu:")
    L.append("- **agregado** (Q1, Q2) — lendo nós internos, ~0 linhas;")
    L.append("- **poda multi-coluna** (Q3a, Q3b, Q4a) — lendo só os ramos que "
             "sobrevivem ao min/max de cada coluna materializada;")
    L.append("- **scan cru** — lendo todos os blocos (o baseline interno).")
    L.append("- **agregado categórico** (Q5) — a query que perdia em Q4b vira "
             "leitura de raiz quando `region_counts` existe no nó.")
    L.append("Uma estrutura, várias interpretações — a leitura é escolhida pelo "
             "objetivo da query. É a tese do paradigma, agora em banco de dados.\n")

    L.append("## LEITURA HONESTA\n")
    L.append("- **D1/D2 ganham por construção** — o agregado vive nos nós; o filtro "
             "no eixo certo poda subárvores. Ganho ∝ fanout·log n (agregação) e ∝ "
             "seletividade (poda).")
    L.append("- **D3 é a mesma fronteira do codec** — assim como textura natural "
             "derrota a rampa, valor independente da chave derrota a poda por min/max. "
             "A interpretação (árvore por key) não casa com a query (filtro por valor "
             "espalhado ou por região). Endereço vazio na biblioteca, não falha da "
             "abordagem: uma árvore organizada por região, ou um índice de valor, "
             "casaria — e é literalmente o que bancos reais mantêm (múltiplos índices "
             "= múltiplas interpretações materializadas).")
    L.append("- **Não inventa um banco novo** — Parquet/zone-maps/segment-trees já "
             "fazem isto. O que o PoC prova é a UNIFICAÇÃO: decode progressivo de "
             "imagem e poda de agregação em banco são a MESMA leitura-por-objetivo "
             "sobre hierarquia grátis.")

    out = ROOT / "RESULTS.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nveredicto: D1={v1} D2={v2} D3=REPORTADA")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
