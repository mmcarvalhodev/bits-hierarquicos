"""bhanno — adversarial annotations over a shared substrate, as a .bh envelope.

The BH thesis at full strength: the **matrix of adverse interpretations**. The
same data (the substrate — images, documents, signals) is recorded ONCE, and K
annotators lay down co-registered interpretation layers that may DISAGREE. This
is the wafer terrain generalized from additive layers (RGB+depth+seg) to RIVAL
layers (K labelings that contest each other).

The capability no current format offers: hold K competing interpretations
without duplicating the substrate. Today, K interpretations means K annotated
copies (the heavy substrate stored K times). bhanno stores the substrate once
and co-registers K label layers over it:

    item(id)             the shared substrate of one item             — its block
    layer(annotator)     one annotator's full interpretation          — its layer
    item_views(id)       ALL K interpretations of one item (the matrix)— K small blocks
    disagreements()      where annotators contest — labels only, no substrate
    adjudicate()         majority verdict per item + agreement rate    — labels only
    full()               everything                                    — the baseline

Every reading reports the bytes it ACTUALLY read (real seeks). The honest
baseline for "holding K interpretations" is K independent annotated copies
(substrate duplicated K times). The saving = the substrate stored once; it
scales with how much the shared substrate dominates the per-layer residual —
the same law as the wafer (§3.4 of the study).

Honest boundary: bhanno wins on the SHARED-substrate / co-registered-rival-
layers structure. It does not adjudicate truth — `adjudicate()` reports the
majority and the disagreement, it does not decide who is right. Resolving the
contest is a modeling decision the envelope surfaces, not one it makes.
"""
from __future__ import annotations

import json
import os
import struct
from collections import Counter
from dataclasses import dataclass

MAGIC = b"BHA1"
_U32 = struct.Struct("<I")


class AnnotationStore:
    """Accumulates a substrate + K annotators' labels; serializes as .bha.

    Layout (one blocks area: substrate first, then label layers):

        MAGIC(4)
        header_len(4) + header_json   {dataset_id, n_items, annotators:[...]}
        itab_len(4)   + itab_json      [{id, off, size}, ...]  (substrate locators)
        ltab_len(4)   + ltab_json      {annotator: [{id, off, size}, ...]}
        substrate_block_0 ...          per-item substrate (shared, once)
        label_block_0 ...              per-(annotator,item) label

    The header + itab + ltab are the index. The substrate is stored ONCE; each
    annotator adds only a layer of labels over it.
    """

    def __init__(self, dataset_id: str, annotators: list[str]) -> None:
        self.dataset_id = dataset_id
        self.annotators = list(annotators)
        self._items: dict[str, bytes] = {}
        self._labels: dict[str, dict[str, dict]] = {a: {} for a in annotators}

    def add_item(self, item_id: str, substrate: bytes) -> None:
        self._items[item_id] = substrate

    def add_label(self, annotator: str, item_id: str, label: dict) -> None:
        self._labels[annotator][item_id] = label

    def __len__(self) -> int:
        return len(self._items)

    def save(self, path: str | os.PathLike) -> str:
        offset = 0
        itab = []
        chunks: list[bytes] = []
        # substrate region — each item ONCE
        for item_id, data in self._items.items():
            itab.append({"id": item_id, "off": offset, "size": len(data)})
            chunks.append(data)
            offset += len(data)
        # label region — per annotator, per item
        ltab: dict[str, list[dict]] = {}
        for a in self.annotators:
            entries = []
            for item_id, label in self._labels[a].items():
                payload = json.dumps(label, ensure_ascii=False).encode("utf-8")
                entries.append({"id": item_id, "off": offset, "size": len(payload)})
                chunks.append(payload)
                offset += len(payload)
            ltab[a] = entries

        header = json.dumps({
            "dataset_id": self.dataset_id, "n_items": len(self._items),
            "annotators": self.annotators,
        }, ensure_ascii=False).encode("utf-8")
        itab_b = json.dumps(itab, ensure_ascii=False).encode("utf-8")
        ltab_b = json.dumps(ltab, ensure_ascii=False).encode("utf-8")

        with open(path, "wb") as f:
            f.write(MAGIC)
            for blob in (header, itab_b, ltab_b):
                f.write(_U32.pack(len(blob)))
                f.write(blob)
            for c in chunks:
                f.write(c)
        return str(path)


@dataclass
class ReadStats:
    """How much a reading actually cost — measured, not claimed."""

    bytes_read: int
    blocks_read: int
    file_size: int

    @property
    def fraction(self) -> float:
        return self.bytes_read / self.file_size if self.file_size else 0.0


class AnnotationReader:
    """Opens a .bha and serves the readings with real seeks.

    On open it reads only the index (header + item table + label table). The
    substrate and label blocks are read on demand.
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = str(path)
        self.file_size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            if f.read(4) != MAGIC:
                raise ValueError("not a .bha file (bhanno)")
            self.header = json.loads(self._read_blob(f))
            self.itab = json.loads(self._read_blob(f))
            self.ltab = json.loads(self._read_blob(f))
            self._blocks_start = f.tell()
        self.annotators = self.header["annotators"]
        # index bytes = magic + the three length-prefixed blobs
        self._index_bytes = self._blocks_start - 0
        self._item_by_id = {e["id"]: e for e in self.itab}
        self._layer = {a: {e["id"]: e for e in self.ltab.get(a, [])}
                       for a in self.annotators}

    @staticmethod
    def _read_blob(f) -> bytes:
        (n,) = _U32.unpack(f.read(4))
        return f.read(n)

    # ---- reading 1: one item's shared substrate --------------------------
    def item(self, item_id: str) -> tuple[bytes | None, ReadStats]:
        e = self._item_by_id.get(item_id)
        if e is None:
            return None, ReadStats(self._index_bytes, 0, self.file_size)
        return self._read(e), ReadStats(self._index_bytes + e["size"], 1, self.file_size)

    # ---- reading 2: one annotator's whole interpretation -----------------
    def layer(self, annotator: str) -> tuple[dict, ReadStats]:
        entries = self.ltab.get(annotator, [])
        out, read = {}, self._index_bytes
        with open(self.path, "rb") as f:
            for e in entries:
                f.seek(self._blocks_start + e["off"])
                out[e["id"]] = json.loads(f.read(e["size"]))
                read += e["size"]
        return out, ReadStats(read, len(entries), self.file_size)

    # ---- reading 3: ALL interpretations of one item (the adverse matrix) -
    def item_views(self, item_id: str) -> tuple[dict, ReadStats]:
        out, read, n = {}, self._index_bytes, 0
        with open(self.path, "rb") as f:
            for a in self.annotators:
                e = self._layer[a].get(item_id)
                if e is None:
                    continue
                f.seek(self._blocks_start + e["off"])
                out[a] = json.loads(f.read(e["size"]))
                read += e["size"]
                n += 1
        return out, ReadStats(read, n, self.file_size)

    # ---- reading 4: where annotators contest (labels only, no substrate) -
    def disagreements(self, field: str = "class") -> tuple[list[dict], ReadStats]:
        labels, stats = self._read_all_labels()
        contested = []
        for item_id in (e["id"] for e in self.itab):
            votes = {a: labels[a][item_id][field]
                     for a in self.annotators if item_id in labels[a]}
            if len(set(votes.values())) > 1:  # not unanimous
                tally = Counter(votes.values())
                top, n = tally.most_common(1)[0]
                contested.append({
                    "id": item_id, "votes": votes,
                    "majority": top if n * 2 > sum(tally.values()) else None,
                    "agreement": n / sum(tally.values()),
                })
        return contested, stats

    # ---- reading 5: adjudication summary (labels only) -------------------
    def adjudicate(self, field: str = "class") -> tuple[dict, ReadStats]:
        labels, stats = self._read_all_labels()
        majority, unanimous, contested = {}, 0, 0
        for item_id in (e["id"] for e in self.itab):
            votes = [labels[a][item_id][field]
                     for a in self.annotators if item_id in labels[a]]
            tally = Counter(votes)
            top, n = tally.most_common(1)[0]
            majority[item_id] = top if n * 2 > len(votes) else None
            if len(tally) == 1:
                unanimous += 1
            else:
                contested += 1
        n_items = len(self.itab)
        return {
            "n_items": n_items, "n_annotators": len(self.annotators),
            "unanimous": unanimous, "contested": contested,
            "agreement_rate": round(unanimous / n_items, 3) if n_items else 0,
            "majority": majority,
        }, stats

    # ---- baseline: everything --------------------------------------------
    def full(self) -> tuple[dict, ReadStats]:
        out = {"items": {}, "labels": {}}
        with open(self.path, "rb") as f:
            for e in self.itab:
                f.seek(self._blocks_start + e["off"])
                out["items"][e["id"]] = f.read(e["size"])
            for a in self.annotators:
                out["labels"][a] = {}
                for e in self.ltab.get(a, []):
                    f.seek(self._blocks_start + e["off"])
                    out["labels"][a][e["id"]] = json.loads(f.read(e["size"]))
        return out, ReadStats(self.file_size, len(self.itab) + sum(
            len(v) for v in self.ltab.values()), self.file_size)

    # ---- storage comparison: shared substrate vs K independent copies ----
    def storage_comparison(self) -> dict:
        substrate = sum(e["size"] for e in self.itab)
        labels = sum(e["size"] for a in self.annotators for e in self.ltab.get(a, []))
        k = len(self.annotators)
        independent = k * substrate + labels   # each copy carries the full substrate
        return {
            "substrate_bytes": substrate, "label_bytes": labels,
            "annotators": k, "bha_bytes": self.file_size,
            "independent_copies_bytes": independent,
            "saving": round(independent / self.file_size, 2) if self.file_size else 0,
        }

    def _read_all_labels(self) -> tuple[dict, ReadStats]:
        labels: dict[str, dict] = {a: {} for a in self.annotators}
        read, n = self._index_bytes, 0
        with open(self.path, "rb") as f:
            for a in self.annotators:
                for e in self.ltab.get(a, []):
                    f.seek(self._blocks_start + e["off"])
                    labels[a][e["id"]] = json.loads(f.read(e["size"]))
                    read += e["size"]
                    n += 1
        return labels, ReadStats(read, n, self.file_size)

    def _read(self, e: dict) -> bytes:
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start + e["off"])
            return f.read(e["size"])
