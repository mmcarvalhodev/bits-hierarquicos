"""Gate de correção cripto — prova válida verifica, adulterada falha."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bhmerkle import MerkleTree, Proof  # noqa: E402


def items(n: int, salt: bytes = b"") -> list[bytes]:
    return [b"record-%d" % i + salt for i in range(n)]


@pytest.mark.parametrize("n", [1, 2, 3, 5, 8, 1000, 1024, 1025])
def test_prove_verify_roundtrip(n):
    t = MerkleTree(items(n))
    root, _ = t.commit()
    for i in [0, n // 2, n - 1]:
        proof, _ = t.prove(i)
        ok, _ = MerkleTree.verify(root, items(n)[i], proof)
        assert ok, f"prova válida falhou em n={n}, i={i}"


def test_deterministic_root():
    assert MerkleTree(items(500)).root == MerkleTree(items(500)).root


def test_tampered_item_fails_verification():
    n = 256
    t = MerkleTree(items(n))
    proof, _ = t.prove(42)
    ok, _ = MerkleTree.verify(t.root, b"WRONG-ITEM", proof)
    assert not ok


def test_wrong_index_fails():
    n = 256
    t = MerkleTree(items(n))
    proof, _ = t.prove(42)
    # usar a prova de 42 para "provar" o item 43 deve falhar
    ok, _ = MerkleTree.verify(t.root, items(n)[43], proof)
    assert not ok


def test_forged_proof_fails():
    n = 64
    t = MerkleTree(items(n))
    proof, _ = t.prove(10)
    forged = Proof(index=10, siblings=[b"\x00" * 32 for _ in proof.siblings])
    ok, _ = MerkleTree.verify(t.root, items(n)[10], forged)
    assert not ok


def test_multiproof_roundtrip():
    n = 1024
    idxs = [3, 4, 5, 200, 201, 777]
    data = items(n)
    t = MerkleTree(data)
    proof, _ = t.prove_many(idxs)
    ok, _ = MerkleTree.verify_many(t.root, {i: data[i] for i in idxs}, proof)
    assert ok


def test_multiproof_tampered_item_fails():
    n = 1024
    idxs = [10, 11, 12, 513]
    data = items(n)
    t = MerkleTree(data)
    proof, _ = t.prove_many(idxs)
    supplied = {i: data[i] for i in idxs}
    supplied[11] = b"tampered"
    ok, _ = MerkleTree.verify_many(t.root, supplied, proof)
    assert not ok


def test_multiproof_requires_matching_indices():
    data = items(128)
    t = MerkleTree(data)
    proof, _ = t.prove_many([1, 2, 3])
    ok, _ = MerkleTree.verify_many(t.root, {1: data[1], 2: data[2]}, proof)
    assert not ok


def test_any_tamper_changes_root():
    n = 300
    base = MerkleTree(items(n))
    for i in [0, 150, 299]:
        mod = items(n)
        mod[i] = b"tampered"
        assert MerkleTree(mod).root != base.root


def test_locate_tamper_exact():
    n = 1000
    base = MerkleTree(items(n))
    for victim in [0, 1, 499, 998, 999]:
        mod = items(n)
        mod[victim] = b"tampered-here"
        other = MerkleTree(mod)
        idx, _ = base.locate_tamper(other)
        assert idx == victim, f"localizou {idx}, esperado {victim}"


def test_locate_tamper_none_when_equal():
    t1 = MerkleTree(items(128))
    t2 = MerkleTree(items(128))
    idx, _ = t1.locate_tamper(t2)
    assert idx is None


def test_empty_rejected():
    with pytest.raises(ValueError):
        MerkleTree([])
