# Provenance and validation status (3 November 2026)

## Stable Wikipedia revisions
- Musée d’Orsay: https://en.wikipedia.org/w/index.php?title=Mus%C3%A9e_d%27Orsay&oldid=1379299233 (9 October 2026)
- Gare d’Orsay: https://en.wikipedia.org/w/index.php?title=Gare_d%27Orsay&oldid=1370978995 (24 August 2026)
Both revisions are the most recent before the stated research snapshot, 19 October 2026. Historical edition links are now embedded in `data/tei.xml`. These links do not establish that the running text was copied exactly from those revisions; that correspondence should be checked independently.

## Authority verification
- Wikidata Q23402 = Musée d’Orsay (confirmed against Wikidata page).
- Wikidata Q2698691 = Gare d’Orsay (confirmed against Wikidata page).
- Wikidata Q23402 lists VIAF 130307757 and ISNI 0000000121572575, matching TEI references.
- The remaining VIAF, ISNI, ULAN and LOC links have not all been manually audited. Thus authority verification remains partial.

## TEI
- XML parser and local cross-reference checks run using `python validate_tei.py`.
- Full TEI P5 schema validation requires official schema file; run `python validate_tei.py /path/to/tei_all.rng`. Official TEI P5 schema: https://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng
- Do not claim schema validation passed without running it.

## Images
The archive supplied in this conversation does not contain the 17 original image files. They could not be recovered reliably from the local files; no unrelated images have been substituted. Use `restore_images.py` after providing original assets, check corresponding attribution.
