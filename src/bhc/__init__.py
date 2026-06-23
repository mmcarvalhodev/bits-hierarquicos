"""BHC — codec experimental de Bits Hierárquicos (MVP, spec v1.0)."""
from .decoder import decode_full, decode_progressive, decode_roi
from .encoder import encode
from .structure_map import decode_structure_map

__all__ = [
    "encode", "decode_full", "decode_progressive", "decode_roi",
    "decode_structure_map",
]
