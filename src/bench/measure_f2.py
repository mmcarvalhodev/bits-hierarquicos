"""Medição F2 — curvas C1 (progressivo) e C2 (ROI) em frames 4K."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench import corpus
from bhc import decode_progressive, decode_roi, encode

W, H = 3840, 2160
# nível → resolução efetiva do preview (grade 2^k sobre padding 4096)
TARGETS = [("thumb~256", 8), ("~480p", 9), ("~1080p", 11), ("4K", 12)]
ROIS = [
    ("1% área", (1700, 950, 384, 216)),
    ("6% área", (1400, 800, 960, 540)),
    ("25% área", (960, 540, 1920, 1080)),
]

for name, img in [
    ("shapes", corpus.shapes(W, H)),
    ("gradient", corpus.gradient(W, H)),
    ("noise", corpus.noise(W, H)),
]:
    blob, stats = encode(img, pyramid=True)
    print(f"\n=== {name} — arquivo {len(blob) / 1e6:.2f} MB "
          f"(raw {img.nbytes / 1e6:.1f} MB) ===")
    print("C1 progressivo:")
    for label, level in TARGETS:
        _, info = decode_progressive(blob, max_level=level)
        print(f"  {label:10s} nível {level:2d}  bytes={info['bytes_read'] / 1e6:8.3f} MB"
              f"  fração={info['fraction']:7.2%}")
    print("C2 ROI (payload lido / payload total | seeks):")
    for label, (x, y, w, h) in ROIS:
        _, info = decode_roi(blob, x, y, w, h)
        print(f"  {label:10s} área={info['roi_area_fraction']:6.2%}"
              f"  payload={info['payload_fraction']:7.2%}"
              f"  total lido={info['fraction']:7.2%}"
              f"  seeks={info['seeks']:,}")
