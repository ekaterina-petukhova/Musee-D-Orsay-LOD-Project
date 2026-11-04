# Submission checklist

1. Review `methods.html`, `representation.html` and the TEI XML against course guidelines.
2. Confirm completeness of Wikipedia text and record a stable source revision/permalink.
3. Validate TEI against its schema (XML well-formedness alone is not enough).
4. Check authority record equivalences manually and OWL schema/property modelling.
5. Copy licensed historical images into `images/` and check credits.
6. Verify all navigation and download links after deployment on GitHub Pages.
7. Send live project URL to course instructors at least two days before the oral exam.

Regenerate after intentional TEI changes: `python3 rebuild.py`. Then regenerate all diagrams from current CSV/RDF if necessary.


## Wikipedia-attested historical enrichment (19 October 2026)
Based on https://en.wikipedia.org/wiki/Mus%C3%A9e_d%27Orsay (History): Gare d’Orsay historic-monument listing and design competition (1978); Gae Aulenti selection (1981); museum opening (December 1986). Time-span resources for 1900, 1978, 1981 and 1986 are CIDOC CRM modelling decisions grounded in dates in the article. Original 14 selected featured entities are unchanged. Current RDF: 210 triples; 29 project resources. Re-run `python rebuild.py` for repeatable conversion; the independent enrichment is recorded in `data/tei.xml` and converter.

## Post-repair audit (3 November 2026)
- Fixed historical Wikipedia version URLs recorded in `data/tei.xml`; see `PROVENANCE_AND_VALIDATION.md`.
- Structural and local-reference TEI checks pass (`python validate_tei.py`). Official Relax NG schema validation is still outstanding.
- The 17 image assets are absent from the supplied source archive; use `restore_images.py` with the authentic original image directory (and verify image licenses). Images have **not** been recovered.
- Authority IDs were spot-checked; full manual review remains necessary.

## Academic review update
Read `FINAL_ACADEMIC_AUDIT.md` before submission. Vocabulary claims and OWL alignment were corrected and dataset metadata was added. Original photos, full TEI Relax NG validation and remote URI verification still require action.


**Update 2026-11-04:** See `FINAL_TECHNICAL_HANDOFF.md` for the latest test status and replacement image placeholders. Original images and official TEI P5 schema verification are not claimed as completed.
