"""Testes do bhmem — correção como portão antes de qualquer alegação de ganho."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bhmem import Memory, MemoryReader, MemoryStore  # noqa: E402

T0 = 1_700_000_000.0


def _store() -> MemoryStore:
    s = MemoryStore()
    n = 0
    for topic, reps in [("a", 5), ("b", 3), ("c", 7)]:
        for k in range(reps):
            s.add(Memory(id=f"m{n:03d}", ts=T0 + n * 100, kind="fact",
                         topic=topic, text=f"texto {topic} {k}", source=f"src{n}"))
            n += 1
    return s


@pytest.fixture()
def bh(tmp_path) -> MemoryReader:
    p = tmp_path / "mem.bh"
    _store().save(p)
    return MemoryReader(p)


def test_roundtrip_preserva_todas_as_memorias(bh: MemoryReader) -> None:
    mems, stats = bh.full()
    assert len(mems) == 15
    assert {m["id"] for m in mems} == {f"m{n:03d}" for n in range(15)}
    assert stats.bytes_read == bh.file_size  # full lê o arquivo inteiro


def test_recall_devolve_so_o_topico(bh: MemoryReader) -> None:
    mems, stats = bh.recall("b")
    assert len(mems) == 3
    assert all(m["topic"] == "b" for m in mems)
    assert stats.blocks_read == 1  # leu UM bloco, não todos


def test_recall_topico_inexistente(bh: MemoryReader) -> None:
    mems, stats = bh.recall("zzz")
    assert mems == []
    assert stats.blocks_read == 0


def test_summary_nao_le_blocos(bh: MemoryReader) -> None:
    view, stats = bh.summary()
    assert {e["topic"] for e in view} == {"a", "b", "c"}
    assert stats.blocks_read == 0
    # o resumo é estritamente mais barato que ler tudo
    _, full_stats = bh.full()
    assert stats.bytes_read < full_stats.bytes_read


def test_since_filtra_por_tempo(bh: MemoryReader) -> None:
    cutoff = T0 + 10 * 100  # memórias m010..m014
    mems, stats = bh.since(cutoff)
    assert {m["id"] for m in mems} == {f"m{n:03d}" for n in range(10, 15)}
    assert all(m["ts"] >= cutoff for m in mems)
    # só deve ter lido o(s) bloco(s) que tocam a janela, não todos os 3
    assert stats.blocks_read <= 2


def test_provenance_le_so_um_bloco(bh: MemoryReader) -> None:
    prov, stats = bh.provenance("m007")
    assert prov is not None
    assert prov["id"] == "m007"
    assert prov["source"] == "src7"
    assert prov["topic"] == "b"  # a=m000..m004, b=m005..m007, c=m008..m014
    assert stats.blocks_read == 1


def test_provenance_id_inexistente(bh: MemoryReader) -> None:
    prov, stats = bh.provenance("nao_existe")
    assert prov is None
    assert stats.blocks_read == 0


def test_leitura_seletiva_e_mais_barata_que_full(bh: MemoryReader) -> None:
    _, recall_stats = bh.recall("b")
    _, full_stats = bh.full()
    assert recall_stats.bytes_read < full_stats.bytes_read
    assert recall_stats.fraction < 1.0


def test_arquivo_invalido_rejeitado(tmp_path) -> None:
    bad = tmp_path / "bad.bh"
    bad.write_bytes(b"NOPE" + b"\x00" * 20)
    with pytest.raises(ValueError):
        MemoryReader(bad)
