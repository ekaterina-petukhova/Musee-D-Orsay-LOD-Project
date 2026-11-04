# Final verification — 4 November 2026

## Confirmed locally
- `data/tei.xml`: well-formed XML, TEI namespace and key document sections present.
- Local TEI ID/reference integrity checked for **multi-valued** attributes `active`, `passive`, `ref`, `target`, `ana`, and related TEI pointing attributes. This fixes a blind spot in the earlier validation script.
- The documented rebuild command `python rebuild.py` completes for TEI → RDF/Turtle and TEI → HTML. SHA-256 of `data/rdf.ttl` and source TEI are unchanged by rebuild.
- `data/rdf.ttl` and `data/rdf.jsonld` each parse to 210 RDF triples. `diagrams/orsay_ontology.ttl` parses to 90 triples.
- `verify_project.py` reports zero missing local references and zero missing images. **The images are editorial placeholders, not recovered originals.**
- The ZIP archive passed Python ZIP CRC integrity testing.

## Not confirmed: important limits
- **Formal TEI P5 Relax NG validation is NOT complete.** The current official general TEI P5 schema is published at https://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng (web page confirmed), but the file itself could not be retrieved into the validation environment. Download it to your computer and run `python validate_tei.py /path/to/tei_all.rng` from this folder. This may report additional schema-level errors that are not covered by structural tests.
- The deployed GitHub Pages website could not be opened successfully with the available browser service. These are tests of local project files, **not** of the currently published version.
- Original licensed photographs/artworks are missing. The present illustrations are clearly labeled placeholders. Publication rights for replacement images must be checked.
- Source-text matching against pinned Wikipedia revision text, and exhaustive live dereference checks of external authority IDs, have not been completed.

## Deployment
Upload the contents of `orsay_work/` to the **root** of the `Musee-D-Orsay-LOD-Project` repository, or configure GitHub Pages to publish from the folder containing `index.html`. Existing public pages do not automatically update from this ZIP. After publishing, check the main page, TEI page, RDF download, diagrams, and the full-page layout on mobile and desktop.
