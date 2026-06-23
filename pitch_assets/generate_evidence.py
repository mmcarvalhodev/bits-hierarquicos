"""Painel de evidências — os testes onde o BH foi superior, com o baseline rotulado."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
plt.rcParams.update({"font.size": 9, "figure.dpi": 130, "savefig.bbox": "tight"})
GREEN, BLUE, GRAY = "#2e7d32", "#1565c0", "#90a4ae"

fig, axs = plt.subplots(2, 3, figsize=(12.5, 7))

# 1) Decode-programa (procedural) — vs WebP
ax = axs[0, 0]
fam = ["anéis", "ondas", "xadrez", "grad."]
rat = [2904, 3572, 809, 2096]
ax.bar(fam, rat, color=GREEN)
ax.set_yscale("log"); ax.set_ylabel("× menor que WebP")
for i, v in enumerate(rat):
    ax.text(i, v * 1.15, f"{v:,}×", ha="center", fontsize=8, fontweight="bold")
ax.set_title("Dado gerado por regra → programa", fontweight="bold", fontsize=10)
ax.text(0, 0.92, "vs WebP (SOTA) · reconstrói exato", transform=ax.transAxes,
        fontsize=7.5, color=GRAY)
ax.set_ylim(100, 9000)

# 2) Codec conteúdo casado (gradiente lossy) — vs WebP, qualidade ≥
ax = axs[0, 1]
ax.bar(["WebP", "BH"], [116.7, 2.4], color=[GRAY, BLUE])
for i, (v, q) in enumerate([(116.7, "50,2 dB"), (2.4, "57,9 dB")]):
    ax.text(i, v + 3, f"{v} KB\n{q}", ha="center", fontsize=8, fontweight="bold")
ax.set_ylabel("KB"); ax.set_ylim(0, 145)
ax.set_title("Conteúdo casado (gradiente)", fontweight="bold", fontsize=10)
ax.text(0.5, 0.55, "48× menor\nE qualidade\nmaior", transform=ax.transAxes,
        fontsize=8.5, color=GREEN, fontweight="bold", ha="center")

# 3) União — ler 1 região — vs WebP (capacidade)
ax = axs[0, 2]
regs = ["plano", "grad.", "texto", "diagr."]
ax.bar(np.arange(4) - .2, [4.8] * 4, .4, color=GRAY, label="WebP (lê tudo)")
ax.bar(np.arange(4) + .2, [0.087, 0.096, 0.59, 1.8], .4, color=BLUE, label=".bh (só a região)")
ax.set_xticks(range(4)); ax.set_xticklabels(regs)
ax.set_ylabel("KB lidos"); ax.legend(fontsize=7, loc="upper left")
ax.set_title("Ler UMA região (capacidade)", fontweight="bold", fontsize=10)
ax.text(0.97, 0.5, "3–55×\nmenos\nbytes", transform=ax.transAxes,
        fontsize=8.5, color=GREEN, fontweight="bold", ha="right")

# 4) Composicional / simbólico — vs vetor denso
ax = axs[1, 0]
ax.bar(["vetor\ndenso", "envelope\nBH"], [3070, 8], color=[GRAY, GREEN])
ax.set_yscale("log"); ax.set_ylabel("MB (1M conceitos)")
for i, v in enumerate([3070, 8]):
    ax.text(i, v * 1.3, f"{v} MB", ha="center", fontsize=8, fontweight="bold")
ax.set_title("Dado simbólico / composto", fontweight="bold", fontsize=10)
ax.text(0.97, 0.55, "384× menor\n+ consultas que o\ndenso nem formula",
        transform=ax.transAxes, fontsize=8, color=GREEN, fontweight="bold", ha="right")
ax.set_ylim(3, 9000)

# 5) Wafer — camadas co-registradas (vídeo)
ax = axs[1, 1]
labels = ["indep.", "temporal", "wafer +\ntemporal"]
vals = [1.0, 1.65, 2.13]
ax.bar(labels, vals, color=[GRAY, BLUE, GREEN])
for i, v in enumerate(vals):
    ax.text(i, v + .04, f"{v}×", ha="center", fontsize=8, fontweight="bold")
ax.set_ylabel("× vs independente"); ax.set_ylim(0, 2.5)
ax.set_title("Camadas co-registradas (vídeo)", fontweight="bold", fontsize=10)
ax.text(0, 0.92, "estrutura+redundância compõem", transform=ax.transAxes,
        fontsize=7.5, color=GRAY)

# 6) Face de leitura — âncora (mecanismo já-SOTA)
ax = axs[1, 2]
ax.bar(["banco", "GPU", "Merkle"], [488, 1750, 52103], color=GRAY)
ax.set_yscale("log"); ax.set_ylabel("× vs varredura ingênua")
for i, v in enumerate([488, 1750, 52103]):
    ax.text(i, v * 1.3, f"{v:,}×", ha="center", fontsize=8, fontweight="bold")
ax.set_title("Face de leitura (âncora)", fontweight="bold", fontsize=10)
ax.text(0, 0.92, "mecanismo já-SOTA (OLAP/Merkle):\ncredibilidade, NÃO novidade",
        transform=ax.transAxes, fontsize=7.5, color=GRAY)
ax.set_ylim(100, 200000)

fig.suptitle("As medições, uma a uma — onde o BH foi superior (e contra qual baseline)",
             fontweight="bold", fontsize=13, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(OUT / "04_evidencias.png")
print("gerado: 04_evidencias.png")
