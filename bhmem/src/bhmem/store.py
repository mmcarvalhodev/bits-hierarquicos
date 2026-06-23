"""bhmem — memória de agente como envelope .bh navegável.

A tese do BH aplicada à memória de um agente: em vez de espalhar a memória
por documentos + embeddings + resumos + cache + índices (sistemas separados
que precisam ser sincronizados), grava-se UM envelope hierárquico onde a
ESTRUTURA é parte do formato.

O valor não é "ser menor". É **ler só a parte que você precisa**:

    summary()        lê só o índice (resumos por tópico)      — barato
    recall(topic)    salta para UM ramo e lê só ele           — barato
    since(t)         lê só os ramos que tocam a janela        — barato
    provenance(id)   lê só o bloco que contém a memória       — barato
    full()           lê tudo                                   — a linha de base

Cada leitura reporta os bytes que REALMENTE leu do arquivo (seeks reais),
para que o ganho seja medido, não alegado. A linha de base honesta é o store
plano (JSON/JSONL) que carrega o arquivo inteiro para qualquer consulta.

Escopo honesto (a fronteira do BH, igual ao resto do estudo):
  - O `.bh` ganha em acesso ESTRUTURAL: por tópico (pertencimento), por tempo,
    por proveniência. É leitura seletiva sobre hierarquia explícita.
  - Recall semântico DENSO (vetorial) NÃO é feito aqui — delega-se a um índice
    vetorial (HNSW), que o envelope pode referenciar. O BH convoca o
    especialista; não compete com ele. Ver README.
"""
from __future__ import annotations

import json
import os
import struct
from dataclasses import asdict, dataclass, field

MAGIC = b"BHM1"
_U32 = struct.Struct("<I")


@dataclass
class Memory:
    """Uma memória estruturada do agente."""

    id: str
    ts: float  # tempo unix (segundos)
    kind: str  # fact | event | relation | observation
    topic: str  # pertencimento — o ramo da hierarquia
    text: str
    source: str = ""  # proveniência (de onde veio: ferramenta, url, turno...)
    meta: dict = field(default_factory=dict)


def _topic_summary(topic: str, mems: list[Memory]) -> dict:
    """Resumo de um tópico — o que `summary()` lê sem tocar nos blocos."""
    ordered = sorted(mems, key=lambda m: m.ts)
    kinds: dict[str, int] = {}
    for m in mems:
        kinds[m.kind] = kinds.get(m.kind, 0) + 1
    latest = ordered[-1]
    return {
        "topic": topic,
        "n": len(mems),
        "kinds": kinds,
        "tmin": ordered[0].ts,
        "tmax": latest.ts,
        "latest": latest.text[:80],
    }


class MemoryStore:
    """Acumula memórias e as serializa como envelope .bh.

    Layout do arquivo (posição codifica a hierarquia — sem campo HIERARQUIA):

        MAGIC(4)
        header_len(4)  + header_json    {n_topics, n_mem}
        table_len(4)   + table_json     [{topic, n, kinds, tmin, tmax,
                                          latest, offset, size}, ...]
        idindex_len(4) + idindex_json   {id -> topic}   (só `provenance` lê)
        bloco_tópico_0                  json([memória, ...])
        bloco_tópico_1
        ...

    O header + a tabela são o ÍNDICE DE ESTRUTURA: pequenos, lidos sempre por
    summary/recall/since. O id_index é uma região SEPARADA — só `provenance`
    a carrega, para que o resumo não pague pelo mapa de ids. Os blocos ficam
    no fim e são lidos por seek, só quando a consulta os pede.
    """

    def __init__(self) -> None:
        self._mem: list[Memory] = []

    def add(self, m: Memory) -> None:
        self._mem.append(m)

    def __len__(self) -> int:
        return len(self._mem)

    def _grouped(self) -> dict[str, list[Memory]]:
        groups: dict[str, list[Memory]] = {}
        for m in self._mem:
            groups.setdefault(m.topic, []).append(m)
        return groups

    def save(self, path: str | os.PathLike) -> str:
        groups = self._grouped()
        blocks: dict[str, bytes] = {
            topic: json.dumps([asdict(m) for m in mems], ensure_ascii=False).encode("utf-8")
            for topic, mems in groups.items()
        }
        # offsets relativos ao início da região de blocos
        table = []
        offset = 0
        for topic, mems in groups.items():
            entry = _topic_summary(topic, mems)
            entry["offset"] = offset
            entry["size"] = len(blocks[topic])
            table.append(entry)
            offset += entry["size"]

        header = json.dumps(
            {"n_topics": len(groups), "n_mem": len(self._mem)},
            ensure_ascii=False,
        ).encode("utf-8")
        table_bytes = json.dumps(table, ensure_ascii=False).encode("utf-8")
        id_index = {m.id: m.topic for m in self._mem}
        idindex_bytes = json.dumps(id_index, ensure_ascii=False).encode("utf-8")

        with open(path, "wb") as f:
            f.write(MAGIC)
            f.write(_U32.pack(len(header)))
            f.write(header)
            f.write(_U32.pack(len(table_bytes)))
            f.write(table_bytes)
            f.write(_U32.pack(len(idindex_bytes)))
            f.write(idindex_bytes)
            for topic in groups:
                f.write(blocks[topic])
        return str(path)


@dataclass
class ReadStats:
    """Quanto uma leitura realmente custou — medido, não alegado."""

    bytes_read: int
    blocks_read: int
    file_size: int

    @property
    def fraction(self) -> float:
        return self.bytes_read / self.file_size if self.file_size else 0.0


class MemoryReader:
    """Abre um .bh e serve as múltiplas leituras com seeks reais.

    Ao abrir, lê só o índice (MAGIC + header + tabela). Os blocos são lidos
    sob demanda — é isso que torna `recall`/`since`/`provenance` baratos.
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = str(path)
        self.file_size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            if f.read(4) != MAGIC:
                raise ValueError("não é um arquivo .bh (bhmem)")
            (hlen,) = _U32.unpack(f.read(4))
            self.header = json.loads(f.read(hlen))
            (tlen,) = _U32.unpack(f.read(4))
            self.table = json.loads(f.read(tlen))
            # região do id_index: localizada, mas NÃO lida (lazy)
            (self._idindex_len,) = _U32.unpack(f.read(4))
            self._idindex_start = f.tell()
            self._blocks_start = self._idindex_start + self._idindex_len
        # bytes pagos por summary/recall/since (índice de estrutura só)
        self._index_bytes = 4 + 4 + hlen + 4 + tlen + 4
        self._by_topic = {e["topic"]: e for e in self.table}
        self._id_index: dict[str, str] | None = None  # carregado sob demanda

    # ---- leitura 1: o resumo (só o índice) -------------------------------
    def summary(self) -> tuple[list[dict], ReadStats]:
        view = [
            {k: e[k] for k in ("topic", "n", "kinds", "tmin", "tmax", "latest")}
            for e in self.table
        ]
        return view, ReadStats(self._index_bytes, 0, self.file_size)

    # ---- leitura 2: um ramo (um tópico) ----------------------------------
    def recall(self, topic: str) -> tuple[list[dict], ReadStats]:
        entry = self._by_topic.get(topic)
        if entry is None:
            return [], ReadStats(self._index_bytes, 0, self.file_size)
        block = self._read_block(entry)
        return json.loads(block), ReadStats(
            self._index_bytes + entry["size"], 1, self.file_size
        )

    # ---- leitura 3: uma janela temporal ----------------------------------
    def since(self, t: float) -> tuple[list[dict], ReadStats]:
        out: list[dict] = []
        read = self._index_bytes
        nblocks = 0
        with open(self.path, "rb") as f:
            for entry in self.table:
                if entry["tmax"] < t:
                    continue  # ramo inteiro fora da janela — nem lê
                f.seek(self._blocks_start + entry["offset"])
                block = f.read(entry["size"])
                read += entry["size"]
                nblocks += 1
                out.extend(m for m in json.loads(block) if m["ts"] >= t)
        out.sort(key=lambda m: m["ts"])
        return out, ReadStats(read, nblocks, self.file_size)

    # ---- leitura 4: proveniência de uma memória --------------------------
    def provenance(self, mem_id: str) -> tuple[dict | None, ReadStats]:
        # custo: índice de estrutura + o id_index (carregado agora) + 1 bloco
        self._load_id_index()
        cost = self._index_bytes + self._idindex_len
        topic = self._id_index.get(mem_id)  # type: ignore[union-attr]
        if topic is None:
            return None, ReadStats(cost, 0, self.file_size)
        entry = self._by_topic[topic]
        block = self._read_block(entry)
        mem = next((m for m in json.loads(block) if m["id"] == mem_id), None)
        result = None
        if mem is not None:
            result = {
                "id": mem["id"],
                "topic": topic,
                "source": mem.get("source", ""),
                "ts": mem["ts"],
                "kind": mem["kind"],
            }
        return result, ReadStats(cost + entry["size"], 1, self.file_size)

    def _load_id_index(self) -> None:
        if self._id_index is not None:
            return
        with open(self.path, "rb") as f:
            f.seek(self._idindex_start)
            self._id_index = json.loads(f.read(self._idindex_len))

    # ---- linha de base: ler tudo -----------------------------------------
    def full(self) -> tuple[list[dict], ReadStats]:
        out: list[dict] = []
        nblocks = 0
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start)
            for entry in self.table:
                block = f.read(entry["size"])
                nblocks += 1
                out.extend(json.loads(block))
        return out, ReadStats(self.file_size, nblocks, self.file_size)

    def _read_block(self, entry: dict) -> bytes:
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start + entry["offset"])
            return f.read(entry["size"])
