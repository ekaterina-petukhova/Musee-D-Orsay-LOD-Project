# FINAL TECHNICAL HANDOFF — 4 November 2026

## Completed
- TEI XML parses successfully; local `xml:id` references resolve. Replaced nonstandard `<subtitle>` in `titleStmt` with TEI `title type="sub"`.
- Rebuilt TEI → RDF and TEI → HTML with included scripts.
- RDF Turtle and JSON-LD are isomorphic: **210 triples**.
- OWL and DCAT/VoID metadata files parse; site local assets/links pass: **0 missing files**.
- Added 17 explicitly labeled editorial image placeholders, making all 18 HTML image references resolve. These are **not** original photos, artworks, or portraits.

## Outstanding third-party verification
- **Official TEI P5 Relax NG validation NOT EXECUTED**: the official TEI schema could not be downloaded in this environment. No statement of full TEI P5 conformance is made. Validate using `python validate_tei.py /path/to/tei_all.rng` and fix any resulting schema errors before academic submission. Official schema: https://tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng
- Source text has not been collated word-for-word against the pinned Wikipedia revisions.
- External identity links, remote URI dereferencing and the live GitHub Pages deployment were not verified.
- Replace labeled placeholders with licensed images when originals become available.

## Reproduce
```bash
python validate_tei.py
python rebuild.py
python verify_project.py
```

**Scope:** final offline preflight, not certification or live deployment.
