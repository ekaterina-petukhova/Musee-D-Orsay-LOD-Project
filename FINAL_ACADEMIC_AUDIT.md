# Musée d’Orsay — academic alignment report

**Project revision:** 3 November 2026. Benchmarked against the six Francesca Tomasi course presentations supplied by the student: Introduction to DH & KO; CH Standards; KOS; Dublin Core/XML; Ontologies; Linked Open Data.

## Completed in this revision
1. **Vocabulary accuracy:** corrected public-facing prose to match the existing 210-triple RDF dataset. Actual vocabularies include CIDOC CRM, Schema.org, FOAF (person class), SKOS, Dublin Core Terms, RDF/RDFS/OWL and local `ex:` properties. BIBO and GeoNames are **not** used in the RDF dataset and are no longer claimed as implemented.
2. **Ontology:** expanded `diagrams/orsay_ontology.ttl` with five documented project-specific classes and conservative `rdfs:domain`/`rdfs:range` on 13 of 15 project-specific properties. `concerns` and `resultedIn` intentionally lack global restrictions because their semantic roles vary. It is **not** a full formal reasoner validation.
3. **Dataset metadata:** added `data/dataset.ttl` using DCAT, Dublin Core Terms and VoID with downloadable Turtle and JSON-LD distributions. This is a local static metadata file; it does **not** create an HTTP content-negotiation service, SPARQL endpoint or dereferenceable per-entity URI pages.
4. **Access:** added links to downloadable dataset metadata and OWL ontology on the Representation and Knowledge Organization pages, and HTML Dublin Core metadata in the home page `<head>`. Original page layout is otherwise retained.
5. **Reproducibility:** `python rebuild.py` ran without error; it regenerated the unchanged 210-triple historical graph and `tei.html`. RDF Turtle and JSON-LD parse as isomorphic graphs. `python verify_project.py` reports zero invalid local links other than missing images, and `python validate_tei.py` passes XML and local reference checks.

## Explicit remaining limitations
- **Original image assets:** 17 unique local image files are absent (18 HTML references due to one repeated image). No replacement imagery has been introduced. The student must restore original files and verify their license/credit statements; see `IMAGE_ASSETS_MANIFEST.md`.
- **TEI schema validation:** the official TEI P5 Relax NG schema was not available in this environment. `validate_tei.py` provides a runnable full validation path once downloaded. No claim of full TEI conformance is made.
- **Authority verification:** Wikidata Q23402 (museum) and Q2698691 (station) and selected VIAF/ISNI were previously reviewed, but every URI was **not** remotely checked. The static-site URI paths have not been tested for HTTP dereferencing.
- **Source collation:** the running TEI text has not been independently compared sentence-for-sentence with the pinned Wikipedia revisions. Existing revision references were preserved; they are attribution targets, not proof of textual identity.
- **Publication:** no live deployment, browser visual regression or remote HTTP checks were completed in this environment. HTML files are locally link-checked only.

## Local validation commands
```bash
python validate_tei.py
python validate_tei.py /path/to/official/tei_all.rng
python rebuild.py
python verify_project.py
```

## Academic scope and source connection
- **Presentation 2: CH standards** distinguishes content, structure, value and encoding standards; distinguish these roles in `methods.html` instead of claiming all standards are implemented.
- **Presentation 3: KOS** motivates authority control with stable URIs; `owl:sameAs` and `skos:exactMatch` express different kinds of alignment and should be independently verified.
- **Presentation 4: Dublin Core** motivates resource metadata; `data/dataset.ttl` uses `dcterms:` for dataset description.
- **Presentation 5: Ontologies** motivates classes, relations, domain and range; see `diagrams/orsay_ontology.ttl`.
- **Presentation 6: LOD** specifies publication, persistent identifiers, RDF, linked resources and five-star practices; download links are present, but the live HTTP aspects remain unverified.


**Update 2026-11-04:** See `FINAL_TECHNICAL_HANDOFF.md` for the latest test status and replacement image placeholders. Original images and official TEI P5 schema verification are not claimed as completed.
