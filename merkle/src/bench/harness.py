"""Harness BH Merkle — M1-M3 + escala, emite RESULTS.md com veredicto."""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from bhmerkle import MerkleTree
from bhmerkle.tree import HASH_LEN

ITEM_SIZE = 64  # bytes por registo


def items(n: int) -> list[bytes]:
    return [(b"record-%010d" % i).ljust(ITEM_SIZE, b".") for i in range(n)]


def fmt(n) -> str:
    return f"{n:,}"


def main() -> None:
    N = 1 << 20  # ~1,05M itens
    print(f"construindo árvore de Merkle com {fmt(N)} itens ...", flush=True)
    t0 = time.perf_counter()
    data = items(N)
    tree = MerkleTree(data)
    build_s = time.perf_counter() - t0
    print(f"  construída em {build_s:.1f}s ({fmt(tree.hashes_built)} hashes)", flush=True)

    L = ["# BH MERKLE MVP — RESULTADOS\n"]
    L.append(f"Dataset: {fmt(N)} itens de {ITEM_SIZE} B · SHA-256 · árvore binária.")
    L.append("Métrica primária: **bytes lidos/transmitidos** para a tarefa "
             "(o análogo do bytes-lidos do codec e linhas-lidas do banco).\n")

    # M1 — commitment O(1)
    root, c_info = tree.commit()
    naive_commit = N * HASH_LEN  # guardar um hash por item p/ ter o que checar
    L.append("## VEREDICTO POR ALEGAÇÃO\n")

    # M2 — prova de pertença
    proof, p_info = tree.prove(N // 3)
    ok, v_info = MerkleTree.verify(root, data[N // 3], proof)
    assert ok
    naive_proof = N * HASH_LEN  # transmitir os N hashes p/ recomputar o root
    m2_gain = naive_proof / p_info["bytes_read"]

    many = list(range(700_000, 700_032))
    mproof, mp_info = tree.prove_many(many)
    ok, _ = MerkleTree.verify_many(root, {i: data[i] for i in many}, mproof)
    assert ok
    individual_bytes = sum(tree.prove(i)[1]["bytes_read"] for i in many)

    # M3 — localizar adulteração
    mod = items(N)
    mod[700_000] = b"TAMPERED"
    other = MerkleTree(mod)
    idx, loc_info = tree.locate_tamper(other)
    assert idx == 700_000
    m3_gain = N / loc_info["nodes_read"]

    m1 = "CONFIRMADA" if c_info["bytes_read"] == HASH_LEN else "REFUTADA"
    m2 = "CONFIRMADA" if m2_gain >= 1000 else "PARCIAL"
    m3 = "CONFIRMADA" if loc_info["nodes_read"] < N / 100 else "REFUTADA"

    L.append(f"- **M1 (commitment O(1) ≈ thumbnail): {m1}** — a integridade de "
             f"{fmt(N)} itens cabe em {c_info['bytes_read']} bytes (1 hash).")
    L.append(f"- **M2 (prova O(log n) ≈ ROI): {m2}** — provar pertença custa "
             f"{p_info['nodes_read']} hashes ({fmt(p_info['bytes_read'])} B); "
             f"ingênuo: {fmt(naive_proof)} B. Ganho {m2_gain:,.0f}×.")
    L.append(f"- **M3 (localizar adulteração O(log n) ≈ diff): {m3}** — achou o item "
             f"adulterado lendo {loc_info['nodes_read']} nós; re-hash total leria "
             f"{fmt(N)}. Ganho {m3_gain:,.0f}×.")
    L.append("- **Borda (declarada): auditar TODOS lê tudo; árvore ~dobra o "
             "armazenamento de hashes; Merkle dá integridade, não sigilo.**\n")

    L.append("## TAREFAS — trabalho medido\n")
    L.append("| tarefa | BH lê | baseline ingênuo | ganho |")
    L.append("|---|---|---|---|")
    L.append(f"| Commitment do dataset | {c_info['bytes_read']} B | {fmt(naive_commit)} B "
             f"(hash por item) | {naive_commit / c_info['bytes_read']:,.0f}× |")
    L.append(f"| Prova de pertença | {fmt(p_info['bytes_read'])} B | {fmt(naive_proof)} B "
             f"(os N itens) | {m2_gain:,.0f}× |")
    L.append(f"| Multiprova 32 itens contíguos | {fmt(mp_info['bytes_read'])} B | "
             f"{fmt(individual_bytes)} B (32 provas separadas) | "
             f"{individual_bytes / mp_info['bytes_read']:,.1f}× |")
    L.append(f"| Localizar adulteração | {loc_info['nodes_read']} nós | {fmt(N)} re-hashes "
             f"| {m3_gain:,.0f}× |")

    L.append("\n## ESCALA — a prova cresce com log n, não com n\n")
    L.append("| N | níveis | prova (hashes) | prova (bytes) | ingênuo (bytes) | ganho |")
    L.append("|---|---|---|---|---|---|")
    for bits in [10, 12, 14, 16, 18, 20]:
        n = 1 << bits
        tr = MerkleTree(items(n))
        pr, info = tr.prove(0)
        naive = n * HASH_LEN
        L.append(f"| {fmt(n)} | {tr.depth} | {info['nodes_read']} | "
                 f"{fmt(info['bytes_read'])} | {fmt(naive)} | {naive / info['bytes_read']:,.0f}× |")

    L.append("\n## A MESMA ÁRVORE, CINCO LEITURAS\n")
    L.append("Nenhuma estrutura auxiliar. A MESMA árvore respondeu:")
    L.append("- **commitment** — lê só a raiz (1 hash);")
    L.append("- **prova de pertença** — lê um ramo (log n irmãos);")
    L.append("- **multiprova** — várias folhas compartilham irmãos comuns;")
    L.append("- **localizar adulteração** — desce o ramo divergente (log n);")
    L.append("- **auditoria total** — lê todas as folhas (o baseline interno).")
    L.append("Uma estrutura, várias interpretações — a leitura é escolhida pelo "
             "objetivo. Igual ao codec (thumbnail/ROI/full) e ao banco "
             "(agregado/poda/scan). É a tese, num terceiro terreno.\n")

    L.append("## LEITURA HONESTA\n")
    L.append("- **M1/M2/M3 ganham por construção** — o agregado-hash vive nos nós; "
             "a hierarquia dá prova e localização logarítmicas. Mesma origem do "
             "ganho do thumbnail (codec) e da agregação (banco).")
    L.append("- **A borda é a mesma das outras** — verificar TUDO lê tudo (sem "
             "atalho), como decodar o 4K inteiro ou agregar sem range. O ganho é "
             "em acesso/prova SELETIVOS, não em trabalho total.")
    L.append("- **Não inventa cripto** — Merkle é padrão (blockchain, git, CT). O "
             "PoC prova a UNIFICAÇÃO: verificar-por-Merkle é a mesma "
             "leitura-por-objetivo-sobre-hierarquia-grátis dos outros dois terrenos.")

    out = ROOT / "RESULTS.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nveredicto: M1={m1} M2={m2} M3={m3}")
    print(f"relatório: {out}")


if __name__ == "__main__":
    main()
