"""MerkleTree — a face VERIFICAR do paradigma BH.

A MESMA árvore é lida de quatro formas, cada uma escolhida pelo objetivo:
  commit()        lê só a raiz          — integridade de N itens em 1 hash
  prove(i)        lê um ramo (log n)    — prova de pertença
  locate_tamper() desce o ramo divergente (log n) — qual item mudou
  full_audit()    lê todas as folhas    — o baseline (verificar tudo)

Cada leitura reporta o trabalho: hashes/bytes lidos ou transmitidos —
o análogo do "bytes lidos" do codec e "linhas lidas" do banco.

SHA-256 com domain separation: folha com prefixo 0x00, nó interno 0x01
(defesa clássica contra second-preimage). Não inventa cripto — usa a
construção padrão; a contribuição é mostrar que é o MESMO paradigma.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

HASH_LEN = 32
_LEAF = b"\x00"
_NODE = b"\x01"


def h_leaf(item: bytes) -> bytes:
    return hashlib.sha256(_LEAF + item).digest()


def h_node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(_NODE + left + right).digest()


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


# folha-sentinela determinística para padding
_PAD = h_leaf(b"\x00BHC-PAD")


@dataclass
class Proof:
    index: int
    siblings: list[bytes]   # de baixo para cima

    @property
    def bytes_size(self) -> int:
        return len(self.siblings) * HASH_LEN + 4  # hashes + índice


@dataclass
class MultiProof:
    indices: list[int]
    depth: int
    helpers: list[tuple[int, int, bytes]]  # (level, index, hash)

    @property
    def bytes_size(self) -> int:
        return len(self.helpers) * (HASH_LEN + 8) + len(self.indices) * 4


class MerkleTree:
    def __init__(self, items: list[bytes]):
        if not items:
            raise ValueError("dataset vazio")
        self.n = len(items)
        size = _next_pow2(self.n)
        self.depth = size.bit_length() - 1  # nº de níveis acima das folhas

        leaves = [h_leaf(x) for x in items]
        leaves.extend([_PAD] * (size - self.n))

        # levels[0] = folhas ... levels[depth] = [root]
        self.levels: list[list[bytes]] = [leaves]
        self.hashes_built = self.n  # contabiliza hashes de folha
        while len(self.levels[-1]) > 1:
            cur = self.levels[-1]
            nxt = [h_node(cur[i], cur[i + 1]) for i in range(0, len(cur), 2)]
            self.hashes_built += len(nxt)
            self.levels.append(nxt)

    # ---- leitura 1: COMMITMENT (≈ thumbnail) ----

    def commit(self) -> tuple[bytes, dict]:
        """A integridade de todo o dataset num único hash."""
        return self.levels[-1][0], {"bytes_read": HASH_LEN, "nodes_read": 1}

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    # ---- leitura 2: PROVA DE PERTENÇA (≈ ROI) ----

    def prove(self, i: int) -> tuple[Proof, dict]:
        if not (0 <= i < self.n):
            raise IndexError(i)
        siblings = []
        idx = i
        for lvl in range(self.depth):
            siblings.append(self.levels[lvl][idx ^ 1])
            idx >>= 1
        proof = Proof(index=i, siblings=siblings)
        return proof, {"bytes_read": proof.bytes_size, "nodes_read": len(siblings)}

    @staticmethod
    def verify(root: bytes, item: bytes, proof: Proof) -> tuple[bool, dict]:
        """Verifica com o root confiável + o item + a prova. Lê só a prova."""
        h = h_leaf(item)
        idx = proof.index
        hashes = 1
        for sib in proof.siblings:
            if idx & 1:
                h = h_node(sib, h)
            else:
                h = h_node(h, sib)
            hashes += 1
            idx >>= 1
        ok = h == root
        return ok, {"bytes_read": proof.bytes_size, "hashes_computed": hashes}

    # ---- leitura 3: LOCALIZAR ADULTERAÇÃO (≈ diff progressivo) ----

    def prove_many(self, indices: list[int]) -> tuple[MultiProof, dict]:
        """Prova multiponto: compartilha hashes irmaos entre varios itens."""
        if not indices:
            raise ValueError("indices vazio")
        uniq = sorted(set(indices))
        for i in uniq:
            if not (0 <= i < self.n):
                raise IndexError(i)

        active = set(uniq)
        helpers: list[tuple[int, int, bytes]] = []
        for lvl in range(self.depth):
            next_active = set()
            for idx in sorted(active):
                sib = idx ^ 1
                if sib not in active:
                    helpers.append((lvl, sib, self.levels[lvl][sib]))
                next_active.add(idx >> 1)
            active = next_active

        proof = MultiProof(indices=uniq, depth=self.depth, helpers=helpers)
        return proof, {"bytes_read": proof.bytes_size, "nodes_read": len(helpers)}

    @staticmethod
    def verify_many(
        root: bytes, items_by_index: dict[int, bytes], proof: MultiProof,
    ) -> tuple[bool, dict]:
        """Verifica varios itens contra o mesmo root usando uma multiprova."""
        if sorted(items_by_index) != proof.indices:
            return False, {"bytes_read": proof.bytes_size, "hashes_computed": 0}

        known: dict[tuple[int, int], bytes] = {
            (0, i): h_leaf(items_by_index[i]) for i in proof.indices
        }
        for lvl, idx, h in proof.helpers:
            known[(lvl, idx)] = h

        hashes = len(proof.indices)
        active = set(proof.indices)
        for lvl in range(proof.depth):
            next_active = set()
            for idx in sorted(active):
                parent = idx >> 1
                if parent in next_active:
                    continue
                left = parent * 2
                right = left + 1
                lh = known.get((lvl, left))
                rh = known.get((lvl, right))
                if lh is None or rh is None:
                    return False, {
                        "bytes_read": proof.bytes_size,
                        "hashes_computed": hashes,
                    }
                known[(lvl + 1, parent)] = h_node(lh, rh)
                hashes += 1
                next_active.add(parent)
            active = next_active

        ok = known.get((proof.depth, 0)) == root
        return ok, {"bytes_read": proof.bytes_size, "hashes_computed": hashes}

    def locate_tamper(self, other: "MerkleTree") -> tuple[int | None, dict]:
        """Desce o ramo divergente da raiz à folha. Lê O(log n) nós de cada
        árvore. Retorna o índice da primeira folha real que difere."""
        nodes_read = 0
        if self.root == other.root:
            return None, {"nodes_read": 2}  # leu as duas raízes
        idx = 0
        # desce do topo (levels[depth]) até as folhas (levels[0])
        for lvl in range(self.depth - 1, -1, -1):
            left = idx * 2
            a_left = self.levels[lvl][left]
            b_left = other.levels[lvl][left]
            nodes_read += 2
            if a_left != b_left:
                idx = left
            else:
                idx = left + 1  # a divergência está no irmão direito
        if idx >= self.n:
            idx = None  # divergência caiu no padding (datasets de tamanho diferente)
        return idx, {"nodes_read": nodes_read}

    # ---- leitura 4: AUDITORIA TOTAL (o baseline interno) ----

    def full_audit(self, items: list[bytes]) -> tuple[bool, dict]:
        """Re-hasheia todos os itens e compara com o root. Lê tudo."""
        rebuilt = MerkleTree(items)
        return rebuilt.root == self.root, {"bytes_read": sum(len(x) for x in items),
                                           "items_read": len(items)}
