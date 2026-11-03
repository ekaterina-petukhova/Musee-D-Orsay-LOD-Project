# Musée d’Orsay LODLAM Research Project

Course: Information Science and Cultural Heritage, University of Bologna (2025–2026).

## Pages
- `index.html`: project and 14 featured entities.
- `knowledge.html`: theoretical and conceptual models.
- `representation.html`: TEI, RDF and interactive Knowledge Graph.
- `methods.html`: E/R model; Metadata Analysis & Alignment; Items Description; URI Production; pipeline.
- `team.html`: author and project context.

## Verified local data (current uploads)
- TEI body: selected sections of the Musée d’Orsay Wikipedia article.
- Distinct annotated IDs: 10; total inline annotated mentions: 19.
- Project entity records: 21; original featured entities: 14.
- RDF graph: 210 triples.
- Pipeline: `python3 rebuild.py` (do not add `--import-wikipedia` without intentional re-import).
- Models: `diagrams/TheoreticalModel.csv`, `diagrams/ConceptualModel.csv`; diagram generator `diagrams/generate_model.py`.

## Limitations
- The TEI body consists of selected Wikipedia paragraphs and has not been collated against a fixed Wikipedia revision for a claim of exact transcription.
- Authority links are not all manually confirmed.
- The conceptual model is a Graffoo-inspired visual schema and CSV, not yet a validated machine-readable OWL ontology file.
- Original images were not included among the uploads; copy your own `images/` contents here before publishing.

## Detailed RDF documentation
`methods.html` now contains a complete inventory of 21 project entity URI subjects from `data/rdf.ttl`, per-entity subject–predicate–object tables and 21 downloadable CSV files in `data/entity_csv/`. `data/all_entity_triples.csv` aggregates entity-subject triples. Metadata Alignment uses counts and predicate names from the actual graph, organized by analytical WHO/WHAT/WHERE/WHEN dimensions. 14 research-selected entities are still featured on the homepage. No TEI or RDF statements were changed for this expansion.


## Wikipedia-attested historical enrichment (19 October 2026)
Based on https://en.wikipedia.org/wiki/Mus%C3%A9e_d%27Orsay (History): Gare d’Orsay historic-monument listing and design competition (1978); Gae Aulenti selection (1981); museum opening (December 1986). Time-span resources for 1900, 1978, 1981 and 1986 are CIDOC CRM modelling decisions grounded in dates in the article. Original 14 selected featured entities are unchanged. Current RDF: 210 triples; 29 project resources. Re-run `python rebuild.py` for repeatable conversion; the independent enrichment is recorded in `data/tei.xml` and converter.
