import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, FOAF, DCTERMS, XSD, OWL

TEI_FILE = "tei.xml"
OUTPUT_FILE = "rdf.ttl"

NS = {
    "tei": "http://www.tei-c.org/ns/1.0"
}

BASE = Namespace("https://example.org/orsay/")
WD = Namespace("https://www.wikidata.org/wiki/")
VIAF = Namespace("https://viaf.org/viaf/")
ISNI = Namespace("https://isni.org/isni/")
GEONAMES = Namespace("https://www.geonames.org/")
LOC = Namespace("https://id.loc.gov/authorities/")
SCHEMA = Namespace("https://schema.org/")
BIBO = Namespace("http://purl.org/ontology/bibo/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def local_uri(xml_id):
    return BASE[xml_id]


def xml_id(element):
    return element.attrib.get("{http://www.w3.org/XML/1998/namespace}id")


def clean_text(element):
    if element is None:
        return None
    text = "".join(element.itertext())
    return " ".join(text.split())


def authority_uri(value):
    if not value:
        return None

    value = value.strip()

    if value.startswith("wikidata:"):
        return URIRef(WD[value.replace("wikidata:", "")])
    if value.startswith("viaf:"):
        return URIRef(VIAF[value.replace("viaf:", "")])
    if value.startswith("isni:"):
        return URIRef(ISNI[value.replace("isni:", "")])
    if value.startswith("geonames:"):
        return URIRef(GEONAMES[value.replace("geonames:", "")])
    if value.startswith("loc:"):
        return URIRef(LOC[value.replace("loc:", "")])

    return URIRef(value)


def add_idnos(graph, subject, element):
    for idno in element.findall("tei:idno", NS):
        uri = authority_uri(clean_text(idno))
        if uri:
            graph.add((subject, OWL.sameAs, uri))


def refs_to_uris(refs):
    if not refs:
        return []

    result = []
    for ref in refs.split():
        if ref.startswith("#"):
            result.append(local_uri(ref[1:]))
    return result


def transform_tei_to_rdf():
    tree = ET.parse(TEI_FILE)
    root = tree.getroot()

    g = Graph()

    g.bind("orsay", BASE)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("foaf", FOAF)
    g.bind("dcterms", DCTERMS)
    g.bind("schema", SCHEMA)
    g.bind("bibo", BIBO)
    g.bind("skos", SKOS)
    g.bind("owl", OWL)
    g.bind("wd", WD)
    g.bind("viaf", VIAF)
    g.bind("isni", ISNI)
    g.bind("geonames", GEONAMES)
    g.bind("loc", LOC)

    project = BASE["project"]
    g.add((project, RDF.type, SCHEMA.CreativeWork))
    g.add((project, DCTERMS.title, Literal("From Railway Station to Museum: The Story of the Musée d’Orsay")))
    g.add((project, DCTERMS.subject, Literal("Cultural heritage transformation")))

    # PERSONS
    for person in root.findall(".//tei:listPerson/tei:person", NS):
        xid = xml_id(person)
        if not xid:
            continue

        uri = local_uri(xid)
        name = clean_text(person.find("tei:persName", NS))
        occupation = clean_text(person.find("tei:occupation", NS))

        g.add((uri, RDF.type, FOAF.Person))

        if name:
            g.add((uri, RDFS.label, Literal(name)))
            g.add((uri, FOAF.name, Literal(name)))

        if occupation:
            g.add((uri, SCHEMA.jobTitle, Literal(occupation)))

        add_idnos(g, uri, person)

    # PLACES
    for place in root.findall(".//tei:listPlace/tei:place", NS):
        xid = xml_id(place)
        if not xid:
            continue

        uri = local_uri(xid)
        name = clean_text(place.find("tei:placeName", NS))
        place_type = place.attrib.get("type")

        g.add((uri, RDF.type, SCHEMA.Place))

        if place_type == "museum":
            g.add((uri, RDF.type, SCHEMA.Museum))
        elif place_type == "city":
            g.add((uri, RDF.type, SCHEMA.City))
        elif place_type == "building":
            g.add((uri, RDF.type, SCHEMA.LandmarksOrHistoricalBuildings))

        if name:
            g.add((uri, RDFS.label, Literal(name)))
            g.add((uri, SCHEMA.name, Literal(name)))

        add_idnos(g, uri, place)

    # ORGANIZATIONS
    for org in root.findall(".//tei:listOrg/tei:org", NS):
        xid = xml_id(org)
        if not xid:
            continue

        uri = local_uri(xid)
        name = clean_text(org.find("tei:orgName", NS))

        g.add((uri, RDF.type, FOAF.Organization))

        if name:
            g.add((uri, RDFS.label, Literal(name)))
            g.add((uri, FOAF.name, Literal(name)))

        add_idnos(g, uri, org)

    # EVENTS
    for event in root.findall(".//tei:listEvent/tei:event", NS):
        xid = xml_id(event)
        if not xid:
            continue

        uri = local_uri(xid)
        label = clean_text(event.find("tei:label", NS))
        date_el = event.find("tei:date", NS)

        g.add((uri, RDF.type, SCHEMA.Event))

        if label:
            g.add((uri, RDFS.label, Literal(label)))
            g.add((uri, SCHEMA.name, Literal(label)))

        if date_el is not None:
            when = date_el.attrib.get("when")
            if when:
                g.add((uri, SCHEMA.startDate, Literal(when)))

        add_idnos(g, uri, event)

    # CONCEPTS
    for term in root.findall(".//tei:textClass/tei:keywords/tei:term", NS):
        xid = xml_id(term)
        if not xid:
            continue

        uri = local_uri(xid)
        label = term.text.strip() if term.text else clean_text(term)
        definition = clean_text(term.find("tei:note", NS))

        g.add((uri, RDF.type, SKOS.Concept))

        if label:
            g.add((uri, RDFS.label, Literal(label)))
            g.add((uri, SKOS.prefLabel, Literal(label)))

        if definition:
            g.add((uri, SKOS.definition, Literal(definition)))

        add_idnos(g, uri, term)

    # BIBLIOGRAPHIC AND DIGITAL RESOURCES
    for bibl in root.findall(".//tei:listBibl/tei:bibl", NS):
        xid = xml_id(bibl)
        if not xid:
            continue

        uri = local_uri(xid)
        bibl_type = bibl.attrib.get("type")
        title = clean_text(bibl.find("tei:title", NS))
        note = clean_text(bibl.find("tei:note", NS))

        if bibl_type == "documentary":
            g.add((uri, RDF.type, SCHEMA.Movie))
            g.add((uri, RDF.type, BIBO.AudioVisualDocument))
        elif bibl_type == "website":
            g.add((uri, RDF.type, SCHEMA.WebSite))
        elif bibl_type == "reference":
            g.add((uri, RDF.type, SCHEMA.WebPage))
            g.add((uri, RDF.type, BIBO.Document))
        else:
            g.add((uri, RDF.type, BIBO.Document))

        if title:
            g.add((uri, RDFS.label, Literal(title)))
            g.add((uri, DCTERMS.title, Literal(title)))

        if note:
            g.add((uri, DCTERMS.description, Literal(note)))

        ref_el = bibl.find("tei:ref", NS)
        if ref_el is not None:
            target = ref_el.attrib.get("target")
            if target:
                g.add((uri, SCHEMA.url, URIRef(target)))

        for pers in bibl.findall(".//tei:persName", NS):
            for ref_uri in refs_to_uris(pers.attrib.get("ref")):
                g.add((uri, DCTERMS.creator, ref_uri))

        for resp_stmt in bibl.findall(".//tei:respStmt", NS):
            resp_text = (clean_text(resp_stmt.find("tei:resp", NS)) or "").lower()
            org_name_el = resp_stmt.find("tei:orgName", NS)
            if org_name_el is None:
                continue
            for ref_uri in refs_to_uris(org_name_el.attrib.get("ref")):
                if "publish" in resp_text:
                    g.add((uri, DCTERMS.publisher, ref_uri))
                else:
                    g.add((uri, SCHEMA.provider, ref_uri))

    # RELATIONS
    relation_predicates = {
        "designedBy": SCHEMA.creator,
        "openedFor": DCTERMS.relation,
        "openedOn": SCHEMA.event,
        "transformedInto": DCTERMS.relation,
        "locatedIn": SCHEMA.location,
        "fillsChronologicalGapBetween": DCTERMS.relation,
        "supportedBy": SCHEMA.sponsor,
        "awardedTo": DCTERMS.relation,
        "ledBy": SCHEMA.founder,
        "interiorDesignedBy": SCHEMA.creator,
        "openedAs": SCHEMA.event,
        "housesWorksBy": SCHEMA.creator,
        "representsArtMovement": DCTERMS.subject,
        "hasArchitecturalStyle": SCHEMA.architecturalStyle,
        "representedIn": DCTERMS.isReferencedBy,
        "directedBy": SCHEMA.director,
        "digitallyRepresentedBy": SCHEMA.subjectOf,
        "providedBy": SCHEMA.provider,
        "isCaseOf": DCTERMS.subject,
        "referencedIn": DCTERMS.isReferencedBy,
        "citesAsCaseStudy": DCTERMS.relation,
        "highlightsConcept": DCTERMS.subject,
        "publishedBy": DCTERMS.publisher,
    }

    for relation in root.findall(".//tei:listRelation/tei:relation", NS):
        name = relation.attrib.get("name")
        active_uris = refs_to_uris(relation.attrib.get("active"))
        passive_uris = refs_to_uris(relation.attrib.get("passive"))

        predicate = relation_predicates.get(name, DCTERMS.relation)

        for active in active_uris:
            for passive in passive_uris:
                g.add((active, predicate, passive))
                g.add((active, BASE["relationName"], Literal(name)))

    # QUOTATIONS
    for quote in root.findall(".//tei:quote", NS):
        text = clean_text(quote)
        if text:
            quote_uri = BASE["quote_from_tei_text"]
            g.add((quote_uri, RDF.type, SCHEMA.Quotation))
            g.add((quote_uri, SCHEMA.text, Literal(text)))
            g.add((quote_uri, RDFS.label, Literal(text)))
            g.add((project, DCTERMS.hasPart, quote_uri))

    g.serialize(destination=OUTPUT_FILE, format="turtle")

    print(f"RDF Turtle file created: {OUTPUT_FILE}")
    print(f"Total triples: {len(g)}")


if __name__ == "__main__":
    transform_tei_to_rdf()