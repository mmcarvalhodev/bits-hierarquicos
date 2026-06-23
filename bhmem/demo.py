"""Demo do bhmem — a memória de um agente como envelope .bh, medida.

Popula uma memória realista (vários tópicos ao longo do tempo), grava como
.bh, e mostra que cada leitura lê só a fração que precisa — contra a linha
de base honesta (store plano que carrega tudo para qualquer consulta).

Rodar:  X:/miniconda3/python.exe X:/bitH/bhmem/demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhmem import Memory, MemoryReader, MemoryStore  # noqa: E402

OUT = Path(__file__).resolve().parent

# --- tempo determinístico (sem Date.now — reprodutível) ---
T0 = 1_700_000_000.0
HOUR = 3600.0
DAY = 24 * HOUR


def build() -> MemoryStore:
    """Memória plausível de um agente que roda há ~90 dias.

    Realista de propósito: dezenas de tópicos (o agente trabalhou em muitas
    coisas), cada um TEMPORALMENTE LOCALIZADO numa janela de poucos dias (você
    foca num tópico, depois move) — só alguns poucos seguem "ativos" até hoje.
    É essa estrutura (muitos ramos + acesso enviesado) que faz a leitura
    seletiva render, exatamente como a lei do estudo prevê.
    """
    store = MemoryStore()
    kinds = ["fact", "event", "relation", "observation"]
    areas = ["projeto", "bug", "infra", "pessoa", "reuniao", "billing",
             "deploy", "review", "incidente", "spec", "ferramenta", "decisao"]
    n = 0
    n_topics = 60
    for ti in range(n_topics):
        area = areas[ti % len(areas)]
        topic = f"{area}_{ti:02d}"
        # janela do tópico: começa em algum dia, dura 2–6 dias
        start_day = (ti * 37) % 86  # espalha determinístico em ~86 dias
        span_days = 2 + (ti % 5)
        # alguns poucos tópicos seguem ativos até "hoje" (dia 90)
        ongoing = ti % 17 == 0
        # densidade variada: tópicos grandes e pequenos
        reps = 8 + (ti * 13) % 60  # 8..67 memórias
        for k in range(reps):
            frac = k / max(reps - 1, 1)
            day = (start_day + frac * span_days) if not ongoing else (start_day + frac * (90 - start_day))
            ts = T0 + day * DAY
            kind = kinds[(ti + k) % len(kinds)]
            store.add(Memory(
                id=f"m{n:05d}",
                ts=ts,
                kind=kind,
                topic=topic,
                text=f"[{topic}] {kind}: nota {k+1} sobre {area} "
                     f"— contexto acumulado do agente neste ramo.",
                source=f"turno#{n} · ferramenta:{'read' if k % 2 else 'bash'}",
                meta={"rep": k, "ongoing": ongoing},
            ))
            n += 1
    return store


def flat_baseline_query(path: Path) -> int:
    """Linha de base honesta: um store plano (JSONL) lê o arquivo INTEIRO
    para qualquer consulta — sem índice de estrutura, sem seek seletivo."""
    return path.stat().st_size


def main() -> None:
    store = build()
    bh_path = OUT / "agent_memory.bh"
    store.save(bh_path)

    # linha de base plana equivalente (mesmas memórias, JSONL cru)
    flat_path = OUT / "agent_memory.jsonl"
    with open(flat_path, "w", encoding="utf-8") as f:
        for m in store._mem:  # noqa: SLF001 (demo)
            f.write(json.dumps(m.__dict__, ensure_ascii=False) + "\n")

    reader = MemoryReader(bh_path)
    flat_size = flat_baseline_query(flat_path)
    bh_size = reader.file_size

    L: list[str] = []
    p = L.append
    p("# bhmem — memória de agente como .bh (demo medida)\n")
    p(f"- memórias: **{len(store)}** · tópicos: **{len(reader.table)}**")
    p(f"- arquivo `.bh`: **{bh_size:,} bytes** · plano JSONL: **{flat_size:,} bytes**\n")
    p("## Cada leitura lê só o que precisa (bytes REAIS lidos do arquivo)\n")
    p("A linha de base plana lê o arquivo **inteiro** para qualquer consulta "
      f"({flat_size:,} B). O `.bh` lê só o ramo pedido.\n")
    p("| leitura | o que devolve | bytes lidos | % do arquivo | vs plano |")
    p("|---|---|---|---|---|")

    def row(label: str, what: str, stats, n: int) -> None:
        ratio = flat_size / stats.bytes_read if stats.bytes_read else float("inf")
        p(f"| `{label}` | {what} ({n}) | {stats.bytes_read:,} B | "
          f"{stats.fraction*100:.1f}% | **{ratio:.0f}× menos** |")

    target_topic = reader.table[7]["topic"]  # um tópico qualquer do meio
    sample_id = "m00000"

    sm, st = reader.summary()
    row("summary()", "resumo de todos os tópicos", st, len(sm))

    rc, st = reader.recall(target_topic)
    row(f"recall('{target_topic}')", "as memórias do tópico", st, len(rc))

    recent_t = T0 + 85 * DAY  # últimos ~5 dias dos 90
    sc, st = reader.since(recent_t)
    row("since(últ. 5d)", "memórias recentes", st, len(sc))

    pv, st = reader.provenance(sample_id)
    row(f"provenance('{sample_id}')", "fonte+caminho de 1 memória", st, 1 if pv else 0)

    fl, st = reader.full()
    row("full()", "tudo (linha de base)", st, len(fl))

    p("\n## O que isto demonstra\n")
    p("- **Não é mais um número de compressão.** É a CAPACIDADE: o agente lê o "
      "resumo, um tópico, uma janela ou a proveniência **sem carregar a memória "
      "inteira**. O custo de cada leitura é proporcional ao que ela pede.")
    p("- **A estrutura é parte do formato.** Pertencimento (tópico), tempo e "
      "proveniência são navegáveis no próprio arquivo — não em quatro sistemas "
      "colados por cima.")
    p("- **Fronteira honesta.** Recall *semântico denso* (vetorial) não é feito "
      "aqui — delega-se a um índice HNSW que o envelope referencia. O `.bh` "
      "convoca o especialista; não compete com ele.")

    out = OUT / "RESULTS_BHMEM_DEMO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    # console (ascii-safe)
    print(f"memorias={len(store)} topicos={len(reader.table)} "
          f"bh={bh_size}B jsonl={flat_size}B")
    for label, fn in [
        ("summary", lambda: reader.summary()),
        (f"recall({target_topic})", lambda: reader.recall(target_topic)),
        ("since(ult.5d)", lambda: reader.since(recent_t)),
        (f"provenance({sample_id})", lambda: reader.provenance(sample_id)),
        ("full", lambda: reader.full()),
    ]:
        _, s = fn()
        ratio = flat_size / s.bytes_read if s.bytes_read else 0
        print(f"  {label:18s} {s.bytes_read:7d} B  {s.fraction*100:5.1f}%  {ratio:5.0f}x menos")
    print(f"relatorio: {out}")


if __name__ == "__main__":
    main()
