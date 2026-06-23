"""Gate de leitura — M1 O(1), M2 O(log n), M3 O(log n), borda lê tudo."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bhmerkle import MerkleTree  # noqa: E402
from bhmerkle.tree import HASH_LEN  # noqa: E402


def items(n: int) -> list[bytes]:
    return [b"record-%d" % i for i in range(n)]


def test_m1_commitment_is_constant_size():
    sizes = []
    for n in [1024, 16384, 262144]:
        _, info = MerkleTree(items(n)).commit()
        sizes.append(info["bytes_read"])
    assert all(s == HASH_LEN for s in sizes)  # O(1) independente de N


def test_m2_proof_is_logarithmic():
    n = 1 << 16  # 65536
    t = MerkleTree(items(n))
    _, info = t.prove(12345)
    # prova = log2(n) hashes irmãos (+ índice)
    assert info["nodes_read"] == int(math.log2(n))
    naive = n * HASH_LEN
    assert info["bytes_read"] < naive / 1000  # ganho > 1000×


def test_m2_proof_grows_log_not_linear():
    counts = []
    for bits in [10, 14, 18]:
        n = 1 << bits
        _, info = MerkleTree(items(n)).prove(0)
        counts.append(info["nodes_read"])
    assert counts == [10, 14, 18]  # cresce com log2, não com N


def test_m2_multiproof_shares_paths():
    n = 1 << 16
    idxs = list(range(1000, 1032))  # clustered ROI-like proof
    t = MerkleTree(items(n))
    _, info = t.prove_many(idxs)
    individual = sum(t.prove(i)[1]["bytes_read"] for i in idxs)
    assert info["bytes_read"] < individual / 4
    assert info["nodes_read"] < len(idxs) * int(math.log2(n)) / 4


def test_m3_localization_is_logarithmic():
    n = 1 << 16
    base = MerkleTree(items(n))
    mod = items(n)
    mod[40000] = b"tampered"
    other = MerkleTree(mod)
    idx, info = base.locate_tamper(other)
    assert idx == 40000
    # O(log n) nós (2 por nível), ≪ N
    assert info["nodes_read"] <= 2 * int(math.log2(n)) + 2
    assert info["nodes_read"] < n / 100


def test_borda_full_audit_reads_everything():
    n = 4096
    t = MerkleTree(items(n))
    ok, info = t.full_audit(items(n))
    assert ok
    assert info["items_read"] == n  # auditar tudo lê tudo — sem ganho


def test_borda_storage_overhead_about_double():
    """A árvore guarda ~2N hashes (folhas + internos): o overhead declarado."""
    n = 1 << 12
    t = MerkleTree(items(n))
    total_nodes = sum(len(lvl) for lvl in t.levels)
    assert total_nodes >= 2 * n - 1  # ~dobro (custo de armazenamento)
    assert total_nodes <= 2 * (1 << 12)  # padded a potência de 2
