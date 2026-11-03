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
