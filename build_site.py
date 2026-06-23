"""Gera o site estático bilíngue (GitHub Pages) a partir dos .md.

Inglês é o padrão (slug base: index.html, master.html, ...).
PT-BR é secundário, com toggle (slug: *.pt.html).
Saída na raiz do repositório. Gráficos: pitch_assets/en/ e pitch_assets/.

Rodar:  X:/miniconda3/python.exe X:/bitH/build_site.py
"""
from __future__ import annotations

from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
ACCENT = "#2e7d32"
GH = "https://github.com/mmcarvalhodev/hierarchical-bits"
DOI = "10.5281/zenodo.20821058"  # concept DOI (always points to the latest version)
DOI_URL = f"https://doi.org/{DOI}"
DOI_BADGE = f"https://zenodo.org/badge/DOI/{DOI}.svg"

# páginas: chave -> {lang: (md, título da aba)}
PAGES = {
    "master": {
        "label": {"en": "Study", "pt": "Estudo"},
        "en": ("BH_MASTER.en.md", "BH — Study (Master)"),
        "pt": ("BH_MASTER.md", "BH — Estudo (Master)"),
    },
    "pitch": {
        "label": {"en": "Pitch", "pt": "Pitch"},
        "en": ("BH_PITCH_APRESENTACAO.en.md", "BH — Pitch"),
        "pt": ("BH_PITCH_APRESENTACAO.md", "BH — Pitch"),
    },
    "visual": {
        "label": {"en": "Visual Pitch", "pt": "Pitch Visual"},
        "en": ("BH_PITCH_VISUAL.en.md", "BH — Visual Pitch"),
        "pt": ("BH_PITCH_VISUAL.md", "BH — Pitch Visual"),
    },
}
ORDER = ["master", "pitch", "visual"]

UI = {
    "en": {"home": "Home", "lang_other": "PT", "repo": "GitHub ↗",
           "foot": ("Hierarchical Bits · © 2025–2026 Márcio M. Carvalho · "
                    f'code under Apache-2.0, docs under CC BY 4.0 · <a href="{GH}">repository</a>')},
    "pt": {"home": "Início", "lang_other": "EN", "repo": "GitHub ↗",
           "foot": ("Bits Hierárquicos · © 2025–2026 Márcio M. Carvalho · "
                    f'código sob Apache-2.0, documentos sob CC BY 4.0 · <a href="{GH}">repositório</a>')},
}

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
.nav a { color: var(--muted); text-decoration: none; font-size: 14px; font-weight: 500; }
.nav a:hover, .nav a.active { color: var(--accent); }
.nav .brand { color: var(--ink); font-weight: 700; margin-right: auto; }
.nav .lang { border: 1px solid var(--accent); color: var(--accent);
             padding: 3px 11px; border-radius: 6px; font-weight: 700; }
.nav .lang:hover { background: var(--accent); color: #fff; }
.nav .gh { border: 1px solid var(--line); padding: 4px 12px; border-radius: 6px; }
main { max-width: 860px; margin: 0 auto; padding: 40px 24px 80px; }
h1, h2, h3, h4 { line-height: 1.25; font-weight: 700; margin: 1.6em 0 .6em; }
h1 { font-size: 2em; margin-top: .2em; }
h2 { font-size: 1.5em; padding-bottom: .3em; border-bottom: 1px solid var(--line); }
h3 { font-size: 1.2em; }
a { color: var(--accent); }
blockquote { margin: 1em 0; padding: .4em 1.1em; border-left: 4px solid var(--accent);
             background: #f3f8f4; border-radius: 0 6px 6px 0; }
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
.hero { padding: 56px 0 8px; }
.hero .lead { font-size: 1.5em; font-weight: 600; line-height: 1.4; }
.hero .sub { color: var(--muted); font-size: 1.05em; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
         gap: 16px; margin: 28px 0; }
.card { border: 1px solid var(--line); border-radius: 10px; padding: 20px;
        text-decoration: none; color: var(--ink); transition: .15s; display: block; }
.card:hover { border-color: var(--accent); box-shadow: 0 4px 16px rgba(0,0,0,.06);
              transform: translateY(-2px); }
.card .t { font-weight: 700; font-size: 1.1em; color: var(--accent); }
.card .d { color: var(--muted); font-size: .92em; margin-top: 6px; }
.pill { display: inline-block; background: #f3f8f4; color: var(--accent);
        border: 1px solid #cfe6d4; border-radius: 999px; padding: 2px 12px;
        font-size: 13px; font-weight: 600; margin-bottom: 18px; }
.nav .doi { border: 1px solid #1565c0; color: #1565c0; padding: 3px 10px;
            border-radius: 6px; font-weight: 700; }
.nav .doi:hover { background: #1565c0; color: #fff; }
.doi-badge { border: 0 !important; border-radius: 0 !important; margin: 12px 0 0 !important; }
.cite { margin-top: 34px; padding: 16px 18px; background: #f6f8fa;
        border: 1px solid var(--line); border-radius: 10px; font-size: .92em; }
.cite .h { font-weight: 700; color: var(--accent); margin-bottom: 6px; }
.cite code { display: block; white-space: pre-wrap; background: #fff; padding: 10px;
             border-radius: 6px; border: 1px solid var(--line); margin-top: 8px; }
"""  % {"accent": ACCENT}


def slug(key: str, lang: str) -> str:
    base = "index" if key == "home" else key
    return f"{base}.html" if lang == "en" else f"{base}.pt.html"


def nav(active_key: str, lang: str) -> str:
    ui = UI[lang]
    items = [(slug("home", lang), ui["home"])]
    items += [(slug(k, lang), PAGES[k]["label"][lang]) for k in ORDER]
    links = "".join(
        f'<a href="{href}" class="{"active" if (active_key=="home" and href==slug("home",lang)) or href==slug(active_key,lang) else ""}">{lbl}</a>'
        for href, lbl in items
    )
    other = "pt" if lang == "en" else "en"
    lang_link = slug(active_key, other)
    brand = "Hierarchical Bits" if lang == "en" else "Bits Hierárquicos"
    return (
        '<div class="nav"><div class="in">'
        f'<a href="{slug("home", lang)}" class="brand">{brand}</a>'
        f'{links}'
        f'<a class="lang" href="{lang_link}" title="Switch language">{ui["lang_other"]}</a>'
        f'<a class="doi" href="{DOI_URL}" title="Zenodo DOI">DOI</a>'
        f'<a class="gh" href="{GH}">{ui["repo"]}</a>'
        '</div></div>'
    )


def page(title: str, active_key: str, lang: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="{'en' if lang == 'en' else 'pt-BR'}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head><body>
{nav(active_key, lang)}
<main>{body}</main>
<div class="foot">{UI[lang]['foot']}</div>
</body></html>
"""


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text, extensions=["extra", "tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5")


def build_doc_pages() -> None:
    for key in ORDER:
        for lang in ("en", "pt"):
            src, title = PAGES[key][lang]
            raw = (ROOT / src).read_text(encoding="utf-8")
            (ROOT / slug(key, lang)).write_text(
                page(title, key, lang, md_to_html(raw)), encoding="utf-8")
            print(f"  {src}  ->  {slug(key, lang)}")


LANDING = {
    "en": {
        "title": "Hierarchical Bits",
        "pill": "Measured study · usable prototype · open source",
        "lead": ('A <b>structural envelope</b>: it represents a heterogeneous asset, '
                 'navigates parts of it without loading everything, and delegates each '
                 'region to the best specialist format.'),
        "sub": ('Most formats force you to pick <i>one</i>: compact (but to see one piece, '
                'decode all of it) or navigable (but structure bolted on top, across several '
                'systems). BH is compact <b>and</b> navigable, in a single file.'),
        "cap_h": "The core capability — not a benchmark",
        "cap_p": ('The heart of BH is not "being smaller". It\'s <b>reading only the part you '
                  'need</b>. The <code>bhmem</code> prototype (agent memory) measures it in real bytes:'),
        "th": ["reading", "bytes read", "vs flat store (reads all)"],
        "rows": [
            ("<code>summary()</code> — digest of all topics", "2.5%", "<b>35× less</b>"),
            ("<code>recall(topic)</code> — one branch", "4.0%", "<b>22× less</b>"),
            ("<code>since(t)</code> — time window", "9.8%", "<b>9× less</b>"),
            ("<code>provenance(id)</code> — source of 1 memory", "10.8%", "<b>8× less</b>"),
        ],
        "cards": [
            ("master.html", "The Study (Master)",
             "9 angles tested, declared method, honest baselines, public self-corrections, "
             "Related Work. Zenodo-ready."),
            ("pitch.html", "Pitch — Presentation",
             "7 slides. Leads with the core capability: read only what you need."),
            ("visual.html", "Pitch — Visual",
             "4 comparative charts + the evidence panel (with the baseline labeled)."),
            (GH, "Code on GitHub",
             "The bhmem prototype (agent memory as .bh), the terrains tested, and how to "
             "reproduce everything."),
        ],
        "quote": ("The value isn't in the compressed block. It's in the structure that knows "
                  "what that block means."),
    },
    "pt": {
        "title": "Bits Hierárquicos",
        "pill": "Estudo medido · protótipo usável · código aberto",
        "lead": ('Um <b>envelope estrutural</b>: representa um ativo heterogêneo, navega por '
                 'partes dele sem carregar tudo, e delega cada região ao melhor formato '
                 'especialista.'),
        "sub": ('A maioria dos formatos te obriga a escolher <i>um</i>: compacto (mas para ver '
                'um pedaço, decodifica tudo) ou navegável (mas é estrutura colada por cima, em '
                'vários sistemas). O BH é compacto <b>e</b> navegável, num arquivo só.'),
        "cap_h": "A capacidade central — não um benchmark",
        "cap_p": ('O coração do BH não é "ser menor". É <b>ler só a parte que você precisa</b>. '
                  'O protótipo <code>bhmem</code> (memória de agente) mede isso em bytes reais:'),
        "th": ["leitura", "bytes lidos", "vs store plano (lê tudo)"],
        "rows": [
            ("<code>summary()</code> — resumo de todos os tópicos", "2,5%", "<b>35× menos</b>"),
            ("<code>recall(tópico)</code> — um ramo", "4,0%", "<b>22× menos</b>"),
            ("<code>since(t)</code> — janela temporal", "9,8%", "<b>9× menos</b>"),
            ("<code>provenance(id)</code> — fonte de 1 memória", "10,8%", "<b>8× menos</b>"),
        ],
        "cards": [
            ("master.pt.html", "O Estudo (Master)",
             "9 ângulos testados, método declarado, baselines honestos, autocorreções "
             "públicas, Related Work. Pronto para Zenodo."),
            ("pitch.pt.html", "Pitch — Apresentação",
             "7 slides. Lidera com a capacidade central: ler só o que precisa."),
            ("visual.pt.html", "Pitch — Visual",
             "4 gráficos comparativos + o painel de evidências (com baseline rotulado)."),
            (GH, "Código no GitHub",
             "O protótipo bhmem (memória de agente em .bh), os terrenos testados, e como "
             "reproduzir tudo."),
        ],
        "quote": ("O valor não está no bloco comprimido. Está na estrutura que sabe o que "
                  "aquele bloco significa."),
    },
}


def build_index() -> None:
    for lang in ("en", "pt"):
        L = LANDING[lang]
        rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in L["rows"])
        cards = "".join(
            f'<a class="card" href="{href}"><div class="t">{t} →</div>'
            f'<div class="d">{d}</div></a>' for href, t, d in L["cards"])
        cite_label = "Cite this work" if lang == "en" else "Como citar"
        published_in = "published as a technical note on Zenodo" if lang == "en" \
            else "publicado como nota técnica no Zenodo"
        cite_html = (
            f'<div class="cite"><div class="h">{cite_label}</div>'
            f'Carvalho, Márcio M. (2026). <i>Hierarchical Bits: A Structural Envelope '
            f'for Orchestrating Representations — Method, Measurements and Boundaries</i> '
            f'({published_in}). '
            f'<a href="{DOI_URL}">https://doi.org/{DOI}</a>.'
            f'<code>DOI: {DOI}</code></div>')
        body = f"""
<div class="hero">
  <div class="pill">{L['pill']}</div>
  <div class="lead">{L['lead']}</div>
  <p class="sub">{L['sub']}</p>
  <a href="{DOI_URL}"><img class="doi-badge" src="{DOI_BADGE}" alt="DOI {DOI}"></a>
</div>
<h2 style="border:0">{L['cap_h']}</h2>
<p>{L['cap_p']}</p>
<table><thead><tr><th>{L['th'][0]}</th><th>{L['th'][1]}</th><th>{L['th'][2]}</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="cards">{cards}</div>
<blockquote>{L['quote']}</blockquote>
{cite_html}
"""
        (ROOT / slug("home", lang)).write_text(
            page(L["title"], "home", lang, body), encoding="utf-8")
        print(f"  {slug('home', lang)}")


if __name__ == "__main__":
    print("gerando site bilíngue (EN padrão · PT toggle):")
    build_index()
    build_doc_pages()
    print("pronto.")
