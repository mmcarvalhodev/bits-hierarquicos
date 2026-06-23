"""Gera os gráficos comparativos do pitch BH (matplotlib)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
plt.rcParams.update({"font.size": 11, "figure.dpi": 130, "savefig.bbox": "tight"})

GREEN = "#2e7d32"
RED = "#c62828"
GRAY = "#90a4ae"
BLUE = "#1565c0"

# ---------- A) MATRIZ DE CAPACIDADES ----------
formats = [".bh (BH-União)", "WebP / AVIF", "PDF", "OLAP / Vector-DB", "AST / JSON"]
caps = ["Compacto", "Leitura\nseletiva", "Orquestra\nespecialistas",
        "Hierarquia +\npertencimento", "Verificável", "Auto-\ndescritivo"]
# 1 = tem, 0 = não tem
M = np.array([
    [1, 1, 1, 1, 1, 1],   # .bh
    [1, 0, 0, 0, 0, 0],   # WebP/AVIF
    [1, 0, 1, 0, 0, 1],   # PDF
    [0, 1, 0, 1, 1, 0],   # OLAP/Vector-DB (verificável p/ Merkle-like)
    [0, 0, 0, 1, 0, 1],   # AST/JSON
])
fig, ax = plt.subplots(figsize=(9, 4.2))
for i in range(len(formats)):
    for j in range(len(caps)):
        ok = M[i, j] == 1
        ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=(GREEN if ok else "#f5f5f5"),
                                   edgecolor="white", lw=2))
        ax.text(j + .5, i + .5, "✓" if ok else "—", ha="center", va="center",
                color="white" if ok else GRAY, fontsize=15, fontweight="bold")
ax.set_xlim(0, len(caps)); ax.set_ylim(0, len(formats))
ax.set_xticks(np.arange(len(caps)) + .5); ax.set_xticklabels(caps, fontsize=9)
ax.set_yticks(np.arange(len(formats)) + .5); ax.set_yticklabels(formats, fontsize=10)
ax.invert_yaxis(); ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("A UNIÃO que ninguém vende: uma estrutura, todas as capacidades",
             fontweight="bold", pad=14)
fig.savefig(OUT / "01_matriz_capacidades.png")
plt.close(fig)

# ---------- B) A UNIÃO (documento) ----------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
# tamanho
ax1.bar(["WebP", ".bh"], [4.8, 2.3], color=[GRAY, BLUE], width=.6)
for x, v in zip([0, 1], [4.8, 2.3]):
    ax1.text(x, v + .08, f"{v} KB", ha="center", fontweight="bold")
ax1.set_title("Tamanho do documento", fontweight="bold")
ax1.set_ylabel("KB"); ax1.set_ylim(0, 5.6)
ax1.text(.5, 5.2, "2,1× menor", ha="center", color=GREEN, fontweight="bold")
# leitura por região
regs = ["plano", "gradiente", "texto", "diagrama"]
bh_read = [0.087, 0.096, 0.59, 1.8]
x = np.arange(len(regs))
ax2.bar(x - .2, [4.8] * 4, .4, color=GRAY, label="WebP (lê tudo)")
ax2.bar(x + .2, bh_read, .4, color=BLUE, label=".bh (lê a região)")
ax2.set_xticks(x); ax2.set_xticklabels(regs)
ax2.set_title("Bytes para ler UMA região", fontweight="bold")
ax2.set_ylabel("KB"); ax2.legend(fontsize=9)
ax2.text(1.5, 4.95, "3–55× menos", ha="center", color=GREEN, fontweight="bold")
fig.suptitle("O mesmo arquivo: menor E navegável", fontweight="bold", y=1.02)
fig.savefig(OUT / "02_uniao.png")
plt.close(fig)

# ---------- C) ONDE RENDE, ONDE DELEGA (mapa honesto, log) ----------
items = [
    ("Procedural (ondas)", 3572, GREEN),
    ("Procedural (anéis)", 2904, GREEN),
    ("Simbólico / composto", 384, GREEN),
    ("Leitura seletiva*", 100, GRAY),   # *já existe em OLAP/Merkle
    ("Documento estruturado", 2.1, GREEN),
    ("Foto + estrutura (mista)", 1.0, GRAY),
    ("Foto natural pura", 0.1, RED),
]
names = [i[0] for i in items]
vals = [i[1] for i in items]
cols = [i[2] for i in items]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
y = np.arange(len(items))
ax.barh(y, vals, color=cols, height=.62)
ax.set_yticks(y); ax.set_yticklabels(names)
ax.set_xscale("log")
ax.axvline(1, color="#37474f", lw=1.2, ls="--")
ax.text(1.15, len(items) - .3, "empate", color="#37474f", fontsize=9)
for yi, v in zip(y, vals):
    ax.text(v * (1.25 if v >= 1 else 0.78), yi, f"{v:g}×", va="center",
            ha="left" if v >= 1 else "right", fontweight="bold", fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("ganho do BH (× menor / menos dados)  —  escala log")
ax.set_title("Onde o BH rende e onde DELEGA — a fronteira honesta",
             fontweight="bold", pad=12)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
fig.text(0.5, -0.02, "* leitura seletiva: mecanismo já existente em OLAP/Merkle "
         "(âncora de credibilidade, não novidade) · vermelho = o BH DELEGA ao WebP/AVIF",
         ha="center", fontsize=8, color=GRAY)
fig.savefig(OUT / "03_onde_rende.png")
plt.close(fig)

print("gerados:", *[p.name for p in sorted(OUT.glob("*.png"))])
