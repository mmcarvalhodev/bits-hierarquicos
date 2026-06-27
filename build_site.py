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
    "principle": {
        "label": {"en": "Principle", "pt": "Princípio"},
        "en": ("BH_PRINCIPLE.md", "BH — The Principle (FCIR)"),
        "pt": ("BH_PRINCIPLE.md", "BH — O Princípio (FCIR) [EN]"),
    },
    "algebra": {
        "label": {"en": "Algebra", "pt": "Álgebra"},
        "en": ("BH_ALGEBRA.md", "BH — Algebra of Interpretations"),
        "pt": ("BH_ALGEBRA.md", "BH — Álgebra das Interpretações [EN]"),
    },
    "conclusion": {
        "label": {"en": "Conclusion", "pt": "Conclusão"},
        "en": ("CONCLUSION.md", "BH — Conclusion (provisional)"),
        "pt": ("CONCLUSION.md", "BH — Conclusão (provisória) [EN]"),
    },
}
# Concept first (Principle, Algebra), then the measured study, then pitch, then
# the provisional conclusion. (Principle/Algebra/Conclusion are English-only for
# now — the PT site links to the English source.)
ORDER = ["principle", "algebra", "master", "pitch", "visual", "conclusion"]

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
        "pill": "A representation principle · measured · open source",
        "lead": ('BH is a <b>representation model</b> where multiple — possibly contradictory '
                 '— interpretations share <b>one immutable substrate</b> and stay queryable, '
                 'without duplicating the data and without forcing them into a single truth.'),
        "sub": ("The heart, in one line: <b>don't duplicate the world every time someone "
                "disagrees with it.</b> Our sweep identified this — rival interpretations "
                "kept as first-class entities — as the property that best distinguishes BH "
                "from the approaches evaluated; we give it a working name: <b>FCIR</b>. "
                "Provisional conclusion: the universal-paradigm claim was <b>not confirmed</b>, "
                "and FCIR already exists in RDF named graphs and standoff annotation — judge it "
                "as a synthesis, not an invention."),
        "cap_h": "What makes it different — and what doesn't",
        "cap_p": ('Storing a substrate once and reading it selectively is <i>already</i> mature '
                  'SOTA (DICOM, COG, lakeFS, S-LoRA…) — BH does not claim that. A '
                  '<a href="' + GH + '/tree/main/applicability">20-domain sweep</a> found the '
                  '<a href="' + GH + '/blob/main/BH_PRINCIPLE.md">FCIR</a> still under-explored: '
                  'the same model held across four very different prototypes —'),
        "th": ["instance", "domain", "the same model, instantiated"],
        "rows": [
            ("<code>bhanno</code>", "rival annotations", "K labelings coexist, adjudication optional — the purest"),
            ("<code>bhmem</code>", "agent memory", "conflicting versions over one history"),
            ("<code>bhckpt</code>", "model checkpoints", "alternative readings of one shared base"),
            ("<code>bhtrace</code>", "traces", "competing lenses over one span tree"),
        ],
        "cards": [
            ("principle.html", "The Principle (FCIR)",
             "What FCIR is, the falsifiable test, and the honest confrontation with Git, "
             "RDF named graphs, CRDTs, bitemporal, standoff, event sourcing."),
            ("algebra.html", "The Algebra",
             "The formal model — operators and laws; FCIR as ⊕ ⊥ α (coexistence "
             "decoupled from adjudication)."),
            ("conclusion.html", "Conclusion (provisional)",
             "The universal-paradigm hypothesis was not confirmed; what survived; the "
             "response to external critique."),
            ("master.html", "The Study (measured)",
             "9 angles tested, declared method, honest baselines, public self-corrections."),
            (GH, "Code on GitHub",
             "Four .bh prototypes (illustrations, not competitors), the sweep, and how to "
             "reproduce everything."),
        ],
        "quote": "Don't duplicate the world every time someone disagrees with it.",
    },
    "pt": {
        "title": "Bits Hierárquicos",
        "pill": "Um princípio de representação · medido · código aberto",
        "lead": ('O BH é um <b>modelo de representação</b> onde múltiplas interpretações — '
                 'possivelmente contraditórias — partilham <b>um substrato imutável</b> e '
                 'permanecem consultáveis, sem duplicar o dado nem as forçar a uma única verdade.'),
        "sub": ('O coração, numa linha: <b>não duplicar o mundo toda vez que alguém discorda '
                'dele.</b> A nossa varredura identificou isto — interpretações rivais mantidas '
                'como entidades de 1ª classe — como a propriedade que melhor distingue o BH '
                'das abordagens avaliadas; damos-lhe um nome de trabalho: <b>FCIR</b>. '
                'Conclusão provisória: a alegação de paradigma universal <b>não foi '
                'confirmada</b>, e a FCIR já existe em RDF named graphs e standoff annotation '
                '— julga-a como síntese, não como invenção.'),
        "cap_h": "O que o torna diferente — e o que não torna",
        "cap_p": ('Guardar um substrato uma vez e ler seletivo <i>já</i> é SOTA maduro '
                  '(DICOM, COG, lakeFS, S-LoRA…) — o BH não reivindica isso. Uma '
                  '<a href="' + GH + '/tree/main/applicability">varredura de 20 domínios</a> '
                  'achou a <a href="' + GH + '/blob/main/BH_PRINCIPLE.md">FCIR</a> ainda pouco '
                  'explorada: o mesmo modelo manteve-se em quatro protótipos muito diferentes —'),
        "th": ["instância", "domínio", "o mesmo modelo, instanciado"],
        "rows": [
            ("<code>bhanno</code>", "anotações rivais", "K rotulagens coexistem, adjudicação opcional — a mais pura"),
            ("<code>bhmem</code>", "memória de agente", "versões conflitantes sobre um histórico"),
            ("<code>bhckpt</code>", "checkpoints de modelo", "leituras alternativas de uma base partilhada"),
            ("<code>bhtrace</code>", "traces", "lentes concorrentes sobre uma árvore de spans"),
        ],
        "cards": [
            ("principle.pt.html", "O Princípio (FCIR)",
             "O que é a FCIR, o teste falsificável, e a confrontação honesta com Git, "
             "RDF named graphs, CRDTs, bitemporal, standoff, event sourcing."),
            ("algebra.pt.html", "A Álgebra",
             "O modelo formal — operadores e leis; FCIR como ⊕ ⊥ α (coexistência "
             "desacoplada da adjudicação)."),
            ("conclusion.pt.html", "Conclusão (provisória)",
             "A hipótese de paradigma universal não foi confirmada; o que sobreviveu; a "
             "resposta à crítica externa."),
            ("master.pt.html", "O Estudo (medido)",
             "9 ângulos testados, método declarado, baselines honestos, autocorreções públicas."),
            (GH, "Código no GitHub",
             "Quatro protótipos .bh (ilustrações, não competidores), a varredura, e como "
             "reproduzir tudo."),
        ],
        "quote": "Não duplicar o mundo toda vez que alguém discorda dele.",
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
<p style="text-align:center; margin: 8px 0 4px;"><img src="pitch_assets/fcir_diagram.svg" alt="FCIR — the model in one picture" style="max-width:100%; border:0;"></p>
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
