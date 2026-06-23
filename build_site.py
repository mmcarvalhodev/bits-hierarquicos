"""Gera o site estático (GitHub Pages) a partir dos .md — tema limpo, gráficos
embutidos. Saída na raiz: index.html + as páginas dos documentos.

Rodar:  X:/miniconda3/python.exe X:/bitH/build_site.py
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
ACCENT = "#2e7d32"

# (arquivo .md, slug de saída, título da aba, rótulo curto na nav)
PAGES = [
    ("BH_MASTER.md", "master.html", "BH — Estudo (Master)", "Estudo"),
    ("BH_PITCH_APRESENTACAO.md", "pitch.html", "BH — Pitch", "Pitch"),
    ("BH_PITCH_VISUAL.md", "visual.html", "BH — Pitch Visual", "Pitch Visual"),
]

CSS = """
:root { --accent: %(accent)s; --ink: #1b1f23; --muted: #57606a;
        --line: #e1e4e8; --bg: #fff; --code-bg: #f6f8fa; }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%%; }
body { margin: 0; color: var(--ink); background: var(--bg);
       font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
       Helvetica, Arial, sans-serif; }
.nav { position: sticky; top: 0; z-index: 10; background: rgba(255,255,255,.92);
       backdrop-filter: blur(6px); border-bottom: 1px solid var(--line); }
.nav .in { max-width: 860px; margin: 0 auto; padding: 12px 24px; display: flex;
           gap: 18px; align-items: center; flex-wrap: wrap; }
.nav a { color: var(--muted); text-decoration: none; font-size: 14px;
         font-weight: 500; }
.nav a:hover, .nav a.active { color: var(--accent); }
.nav .brand { color: var(--ink); font-weight: 700; margin-right: auto; }
.nav .gh { border: 1px solid var(--line); padding: 4px 12px; border-radius: 6px; }
main { max-width: 860px; margin: 0 auto; padding: 40px 24px 80px; }
h1, h2, h3, h4 { line-height: 1.25; font-weight: 700; margin: 1.6em 0 .6em; }
h1 { font-size: 2em; margin-top: .2em; }
h2 { font-size: 1.5em; padding-bottom: .3em; border-bottom: 1px solid var(--line); }
h3 { font-size: 1.2em; }
a { color: var(--accent); }
p, li { color: var(--ink); }
blockquote { margin: 1em 0; padding: .4em 1.1em; border-left: 4px solid var(--accent);
             background: #f3f8f4; color: #24433; border-radius: 0 6px 6px 0; }
blockquote p { margin: .4em 0; }
code { background: var(--code-bg); padding: .15em .4em; border-radius: 5px;
       font: .88em/1.5 "SFMono-Regular", Consolas, "Liberation Mono", monospace; }
pre { background: var(--code-bg); padding: 16px; border-radius: 8px; overflow: auto;
      border: 1px solid var(--line); }
pre code { background: none; padding: 0; font-size: .85em; }
table { border-collapse: collapse; width: 100%%; margin: 1.2em 0; font-size: .95em;
        display: block; overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: 8px 12px; text-align: left; }
th { background: var(--code-bg); font-weight: 600; }
tr:nth-child(even) td { background: #fafbfc; }
img { max-width: 100%%; height: auto; border: 1px solid var(--line);
      border-radius: 8px; margin: 1em 0; }
hr { border: 0; border-top: 1px solid var(--line); margin: 2.4em 0; }
.foot { max-width: 860px; margin: 0 auto; padding: 24px; color: var(--muted);
        font-size: 13px; border-top: 1px solid var(--line); }
/* landing */
.hero { padding: 56px 0 8px; }
.hero .lead { font-size: 1.5em; font-weight: 600; line-height: 1.4; }
.hero .sub { color: var(--muted); font-size: 1.05em; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
         gap: 16px; margin: 28px 0; }
.card { border: 1px solid var(--line); border-radius: 10px; padding: 20px;
        text-decoration: none; color: var(--ink); transition: .15s;
        display: block; }
.card:hover { border-color: var(--accent); box-shadow: 0 4px 16px rgba(0,0,0,.06);
              transform: translateY(-2px); }
.card .t { font-weight: 700; font-size: 1.1em; color: var(--accent); }
.card .d { color: var(--muted); font-size: .92em; margin-top: 6px; }
.pill { display: inline-block; background: #f3f8f4; color: var(--accent);
        border: 1px solid #cfe6d4; border-radius: 999px; padding: 2px 12px;
        font-size: 13px; font-weight: 600; margin-bottom: 18px; }
"""  % {"accent": ACCENT}


def nav(active: str) -> str:
    links = [('index.html', 'Início')] + [(slug, label) for _, slug, _, label in PAGES]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>'
        for href, label in links
    )
    return (
        '<div class="nav"><div class="in">'
        '<a href="index.html" class="brand">Bits Hierárquicos</a>'
        f'{items}'
        '<a class="gh" href="https://github.com/mmcarvalhodev/bits-hierarquicos">GitHub ↗</a>'
        '</div></div>'
    )


def page(title: str, active: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head><body>
{nav(active)}
<main>{body}</main>
<div class="foot">Bits Hierárquicos · © 2025–2026 Márcio M. Carvalho ·
código sob Apache-2.0, documentos sob CC BY 4.0 ·
<a href="https://github.com/mmcarvalhodev/bits-hierarquicos">repositório</a></div>
</body></html>
"""


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["extra", "tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5",
    )


def build_doc_pages() -> None:
    for src, slug, title, _label in PAGES:
        raw = (ROOT / src).read_text(encoding="utf-8")
        body = md_to_html(raw)
        (ROOT / slug).write_text(page(title, slug, body), encoding="utf-8")
        print(f"  {src}  ->  {slug}")


def build_index() -> None:
    cards = [
        ("master.html", "O Estudo (Master)",
         "9 ângulos testados, método declarado, baselines honestos, "
         "autocorreções públicas, Related Work. Pronto para Zenodo."),
        ("pitch.html", "Pitch — Apresentação",
         "7 slides. Lidera com a capacidade central: ler só o que precisa."),
        ("visual.html", "Pitch — Visual",
         "4 gráficos comparativos + o painel de evidências (com baseline rotulado)."),
        ("https://github.com/mmcarvalhodev/bits-hierarquicos", "Código no GitHub",
         "O protótipo bhmem (memória de agente em .bh), os terrenos testados, "
         "e como reproduzir tudo."),
    ]
    cards_html = "".join(
        f'<a class="card" href="{href}"><div class="t">{t} →</div>'
        f'<div class="d">{d}</div></a>'
        for href, t, d in cards
    )
    body = f"""
<div class="hero">
  <div class="pill">Estudo medido · protótipo usável · código aberto</div>
  <div class="lead">Um <b>envelope estrutural</b>: representa um ativo heterogêneo,
  navega por partes dele sem carregar tudo, e delega cada região ao melhor
  formato especialista.</div>
  <p class="sub">A maioria dos formatos te obriga a escolher <i>um</i>: compacto
  (mas para ver um pedaço, decodifica tudo) ou navegável (mas é estrutura colada
  por cima, em vários sistemas). O BH é compacto <b>e</b> navegável, num arquivo só.</p>
</div>

<h2 style="border:0">A capacidade central — não um benchmark</h2>
<p>O coração do BH não é "ser menor". É <b>ler só a parte que você precisa</b>.
O protótipo <code>bhmem</code> (memória de agente) mede isso em bytes reais:</p>

<table>
<thead><tr><th>leitura</th><th>bytes lidos</th><th>vs store plano (lê tudo)</th></tr></thead>
<tbody>
<tr><td><code>summary()</code> — resumo de todos os tópicos</td><td>2,5%</td><td><b>36× menos</b></td></tr>
<tr><td><code>recall(tópico)</code> — um ramo</td><td>4,0%</td><td><b>22× menos</b></td></tr>
<tr><td><code>since(t)</code> — janela temporal</td><td>9,8%</td><td><b>9× menos</b></td></tr>
<tr><td><code>provenance(id)</code> — fonte de 1 memória</td><td>10,8%</td><td><b>8× menos</b></td></tr>
</tbody></table>

<div class="cards">{cards_html}</div>

<blockquote>O valor não está no bloco comprimido. Está na estrutura que sabe o
que aquele bloco significa.</blockquote>
"""
    (ROOT / "index.html").write_text(page("Bits Hierárquicos", "index.html", body),
                                     encoding="utf-8")
    print("  index.html")


if __name__ == "__main__":
    print("gerando site:")
    build_index()
    build_doc_pages()
    print("pronto.")
