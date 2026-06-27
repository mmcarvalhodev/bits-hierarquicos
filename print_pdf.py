"""Gera o PDF da v2 — o arco honesto inteiro, num documento.

Encadeia, com divisores de parte:
  I.   o estudo medido        (BH_MASTER.en.md, a partir do EXECUTIVE SUMMARY)
  II.  o princípio (FCIR)      (BH_PRINCIPLE.md)
  III. a álgebra              (BH_ALGEBRA.md)
  IV.  a conclusão provisória (CONCLUSION.md)

Produz _print_master.html; o Chrome headless converte para BH_MASTER.pdf
(ver ZENODO_SUBMISSION.md). Rodar: X:/miniconda3/python.exe X:/bitH/print_pdf.py
"""
from __future__ import annotations

from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
OUT_HTML = ROOT / "_print_master.html"

TITLE = "Hierarchical Bits — an investigation"
SUBTITLE = ("From a representation paradigm to a property (FCIR), "
            "and its provisional conclusion")
AUTHOR = "Márcio M. Carvalho"
PERIOD = "December 2025 – June 2026"
REPO = "github.com/mmcarvalhodev/hierarchical-bits"
CONCEPT_DOI = "10.5281/zenodo.20821058"

PARTS = [
    ("Part I — The measured study", "BH_MASTER.en.md", "## EXECUTIVE SUMMARY"),
    ("Part II — The principle (FCIR)", "BH_PRINCIPLE.md", None),
    ("Part III — The algebra of interpretations", "BH_ALGEBRA.md", None),
    ("Part IV — Provisional conclusion", "CONCLUSION.md", None),
]

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
* { box-sizing: border-box; }
body { color: #1a1a1a; font: 10.5pt/1.55 Georgia, "Times New Roman", serif; margin: 0; }
.cover { height: 247mm; display: flex; flex-direction: column;
         justify-content: center; page-break-after: always; }
.cover .kicker { font: 600 11pt/1 -apple-system, "Segoe UI", sans-serif;
                 letter-spacing: .18em; text-transform: uppercase; color: #2e7d32; }
.cover h1 { font: 700 32pt/1.12 Georgia, serif; margin: 14px 0 6px; }
.cover .sub { font: 400 15pt/1.4 Georgia, serif; color: #333; margin-bottom: 38px; }
.cover .meta { font: 10.5pt/1.7 -apple-system, "Segoe UI", sans-serif; color: #222; }
.cover .meta b { color: #000; }
.cover .rule { height: 3px; width: 70px; background: #2e7d32; margin: 0 0 26px; }
.cover .foot { margin-top: 40px; font: 9.5pt/1.5 -apple-system, sans-serif; color: #666; }
h1.part { font: 700 21pt/1.2 -apple-system, "Segoe UI", sans-serif; color: #2e7d32;
          page-break-before: always; border-bottom: 3px solid #2e7d32;
          padding-bottom: 6px; margin: 0 0 14px; }
h1, h2, h3, h4 { font-family: -apple-system, "Segoe UI", Helvetica, sans-serif;
                 line-height: 1.25; page-break-after: avoid; }
h2 { font-size: 15pt; border-bottom: 1px solid #ccc; padding-bottom: 3px; margin-top: 22px; }
h3 { font-size: 12pt; margin-top: 16px; }
p { text-align: justify; }
a { color: #1b5e20; text-decoration: none; }
blockquote { margin: 10px 0; padding: 4px 14px; border-left: 3px solid #2e7d32; background: #f4f8f4; }
code { font: 9pt/1.4 "Consolas", monospace; background: #f4f4f4; padding: .1em .35em; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 11px 13px;
      overflow: hidden; page-break-inside: avoid; white-space: pre-wrap; }
pre code { background: none; padding: 0; font-size: 8.6pt; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9.2pt; page-break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #f0f2f4; font-weight: 700; }
img { max-width: 100%; }
hr { border: 0; border-top: 1px solid #ddd; margin: 18px 0; }
"""


def _strip_leading_h1(md: str) -> str:
    """Drop the first top-level '# ...' heading so it doesn't duplicate the Part title."""
    out, dropped = [], False
    for line in md.splitlines():
        if not dropped and line.startswith("# "):
            dropped = True
            continue
        out.append(line)
    return "\n".join(out)


def _md(md: str) -> str:
    return markdown.markdown(
        md, extensions=["extra", "tables", "fenced_code", "sane_lists"],
        output_format="html5")


def main() -> None:
    cover = f"""
<div class="cover">
  <div class="kicker">Technical Note · Open · v2</div>
  <h1>{TITLE}</h1>
  <div class="sub">{SUBTITLE}</div>
  <div class="rule"></div>
  <div class="meta">
    <b>Author:</b> {AUTHOR}<br>
    <b>Study period:</b> {PERIOD}<br>
    <b>License:</b> Creative Commons Attribution 4.0 (CC BY 4.0)<br>
    <b>Repository:</b> {REPO}<br>
    <b>Concept DOI:</b> {CONCEPT_DOI} (a version DOI is assigned when this revision is published)
  </div>
  <div class="foot">An investigation reported at the honest size the evidence supports.
  It tests a strong hypothesis, narrows it under contrary evidence, names what
  survived (FCIR — a working name), and confronts it with the prior art that
  already implements it. Measured; with its boundaries and limitations stated.</div>
</div>
"""
    body = ""
    for part_title, fname, start_marker in PARTS:
        raw = (ROOT / fname).read_text(encoding="utf-8")
        if start_marker:
            idx = raw.find(start_marker)
            raw = raw[idx:] if idx >= 0 else raw
        else:
            raw = _strip_leading_h1(raw)
        body += f'<h1 class="part">{part_title}</h1>\n{_md(raw)}\n'

    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f"<title>{TITLE}</title><style>{CSS}</style></head><body>"
            f"{cover}{body}</body></html>")
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"wrote {OUT_HTML} ({len(PARTS)} parts chained)")


if __name__ == "__main__":
    main()
