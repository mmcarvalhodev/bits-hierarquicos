# Zenodo — publishing v2 (New version)

The v1 record exists (concept DOI **10.5281/zenodo.20821058**, version v1
`…20821059`). This kit publishes **v2** as a *New version* of that record — the
concept DOI keeps pointing to the latest automatically; v1 stays as history.
Nothing is deleted; superseding is the right move for "the document aged".

---

## The file to upload

**`BH_MASTER.pdf`** — the full honest arc in one document (~24 pages, 4 parts:
the measured study → the principle (FCIR) → the algebra → the provisional
conclusion). Regenerate any time:

```
X:/miniconda3/python.exe print_pdf.py
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="X:/bitH/BH_MASTER.pdf" "file:///X:/bitH/_print_master.html"
```

---

## Metadata (paste-ready, updated for v2)

**Title**
```
Hierarchical Bits — an investigation: from a representation paradigm to a property (FCIR), and its provisional conclusion
```

**Authors** — `Carvalho, Márcio M.` · Affiliation: `Independent researcher`

**Resource type** — `Publication` → `Technical note`

**Version** — `2.0`

**License** — `Creative Commons Attribution 4.0 International (CC BY 4.0)`

**Keywords**
```
representation model, concurrent interpretations, FCIR, immutable substrate, named graphs, standoff annotation, data versioning, data formats
```

**Description**
```
Hierarchical Bits (BH) began as a strong hypothesis — that it introduced a new,
general paradigm of representation — and is reported here at the honest size the
evidence supports.

The investigation tested the hypothesis across nine measured angles and a
20-domain survey. Result: the universal-paradigm claim was NOT confirmed — a
shared immutable substrate plus selective reading is already mature state of the
art across most domains (DICOM, COG/STAC, lakeFS, CRAM/tabix, S-LoRA, MAM). What
survived is a narrower, sharper property: keeping multiple — possibly
contradictory — interpretations as first-class, co-registered, persistent
entities over one substrate, with adjudication deferred and optional. We give it
a working name, the First-Class Interpretation Representation (FCIR), formalized
as the decoupling of coexistence from adjudication.

Honestly: FCIR is not a new mechanism — RDF named graphs (with provenance) and
standoff annotation already implement it within their domains; the contribution
is a cross-domain name, a falsifiable test, and an algebra (a specification, not
a verified theory). This version contains the measured study, the principle, the
formal algebra, and a provisional conclusion with its limitations stated. The
work stands as an investigation and as method as much as any single finding.
```

---

## Steps — publish v2 (≈5 clicks; only you can do this)

1. **https://zenodo.org** → log in → open your record
   **https://zenodo.org/records/20821059**.
2. Click **"New version"** (creates a draft copy with the metadata pre-filled).
3. **Files:** delete the old `BH_MASTER.pdf` and upload the new one.
4. Update **Title**, **Description**, **Keywords** with the v2 block above; set
   **Version = 2.0**.
5. **Publish.** You get a **new version DOI**; the **concept DOI
   `10.5281/zenodo.20821058` now resolves to v2 automatically**.

---

## After publishing — nothing breaks

- **README badge, site, citation: no change needed** — they all use the
  *concept* DOI, which is stable and now points to v2.
- *(Optional)* bump `version: "2.0"` in [`CITATION.cff`](CITATION.cff).

---

## Notes

- v1 remains citable and intact; v2 supersedes it under the same concept DOI.
  This is the honest way to retire an aged document — not deletion.
- The repository keeps the **dual license**: code under Apache-2.0
  ([`LICENSE`](LICENSE)), documents under CC BY 4.0 ([`LICENSE-docs.md`](LICENSE-docs.md)).
- A Portuguese PDF can be produced too (chain the `.md` PT sources in
  `print_pdf.py`) for a bilingual record — just ask.
