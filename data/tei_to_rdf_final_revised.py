from pathlib import Path
from typing import Optional

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, OWL, RDF, RDFS, SKOS, XSD


# ============================================================
# 1. FILE PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

XML_FILE = SCRIPT_DIR / "musee_dorsay_tei_final_revised.xml"
OUTPUT_FILE = SCRIPT_DIR / "musee_dorsay_knowledge_graph_final.ttl"


# ============================================================
# 2. XML NAMESPACES
# ============================================================

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

NS = {
    "tei": TEI_NS,
    "xml": XML_NS,
}


# ============================================================
# 3. RDF NAMESPACES
# ============================================================

PROJECT_BASE = Namespace(
    "https://ekaterina-petukhova.github.io/"
    "Musee-D-Orsay-LOD-Project/id/"
)

EX = Namespace(
    "https://ekaterina-petukhova.github.io/"
    "Musee-D-Orsay-LOD-Project/ontology/"
)

CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SCHEMA = Namespace("https://schema.org/")


# ============================================================
# 4. GRAPH
# ============================================================

graph = Graph()

for prefix, namespace in {
    "ex": EX,
    "crm": CRM,
    "schema": SCHEMA,
    "dcterms": DCTERMS,
    "foaf": FOAF,
    "owl": OWL,
    "rdf": RDF,
    "rdfs": RDFS,
    "skos": SKOS,
    "xsd": XSD,
}.items():
    graph.bind(prefix, namespace)


# ============================================================
# 5. HELPERS
# ============================================================

def get_xml_id(element: etree._Element) -> Optional[str]:
    return element.get(f"{{{XML_NS}}}id")


def get_text(element: etree._Element, xpath: str) -> Optional[str]:
    results = element.xpath(xpath, namespaces=NS)

    if not results:
        return None

    first = results[0]

    if isinstance(first, str):
        value = first.strip()
    else:
        value = " ".join(
            text.strip()
            for text in first.itertext()
            if text.strip()
        )

    return value or None


def expand_curie(value: str) -> str:
    value = value.strip()

    prefixes = {
        "project:": (
            "https://ekaterina-petukhova.github.io/"
            "Musee-D-Orsay-LOD-Project/id/"
        ),
        "wikidata:": "https://www.wikidata.org/entity/",
        "viaf:": "https://viaf.org/viaf/",
        "isni:": "https://isni.org/isni/",
        "gettyulan:": "http://vocab.getty.edu/ulan/",
        "gettyaat:": "http://vocab.getty.edu/aat/",
        "loc:": "https://id.loc.gov/authorities/",
    }

    if value.startswith(("http://", "https://")):
        return value

    for prefix, base in prefixes.items():
        if value.startswith(prefix):
            return base + value[len(prefix):]

    return value


def get_project_uri(element: etree._Element) -> URIRef:
    values = element.xpath(
        './/tei:idno[@type="project"]/text()',
        namespaces=NS,
    )

    if values:
        return URIRef(expand_curie(values[0]))

    xml_id = get_xml_id(element)

    if not xml_id:
        raise ValueError("Element has neither project idno nor xml:id.")

    return URIRef(PROJECT_BASE[xml_id])


def add_label(subject: URIRef, label: Optional[str]) -> None:
    if label:
        graph.add((subject, RDFS.label, Literal(label, lang="en")))


def add_description(subject: URIRef, description: Optional[str]) -> None:
    if description:
        graph.add(
            (
                subject,
                DCTERMS.description,
                Literal(description, lang="en"),
            )
        )


def add_dates(element: etree._Element, subject: URIRef) -> None:
    for date_element in element.xpath("./tei:date", namespaces=NS):
        when = date_element.get("when")
        start = date_element.get("from")
        end = date_element.get("to")

        if when:
            datatype = None

            if len(when) == 4:
                datatype = XSD.gYear
            elif len(when) == 7:
                datatype = XSD.gYearMonth
            elif len(when) == 10:
                datatype = XSD.date

            graph.add(
                (
                    subject,
                    DCTERMS.date,
                    Literal(when, datatype=datatype)
                    if datatype
                    else Literal(when),
                )
            )

        if start:
            graph.add(
                (
                    subject,
                    SCHEMA.startDate,
                    Literal(
                        start,
                        datatype=XSD.gYear if len(start) == 4 else XSD.date,
                    ),
                )
            )

        if end:
            graph.add(
                (
                    subject,
                    SCHEMA.endDate,
                    Literal(
                        end,
                        datatype=XSD.gYear if len(end) == 4 else XSD.date,
                    ),
                )
            )


def add_authority_links(
    element: etree._Element,
    subject: URIRef,
    concept: bool = False,
) -> None:
    predicate = SKOS.exactMatch if concept else OWL.sameAs

    for node in element.xpath(
        './/tei:idno[not(@type="project")]',
        namespaces=NS,
    ):
        value = (node.text or "").strip()

        if not value:
            continue

        expanded = expand_curie(value)

        if expanded.startswith(("http://", "https://")):
            graph.add((subject, predicate, URIRef(expanded)))


def add_urls(element: etree._Element, subject: URIRef) -> None:
    for ref in element.xpath(".//tei:ref[@target]", namespaces=NS):
        target = ref.get("target")

        if target and target.startswith(("http://", "https://")):
            graph.add((subject, SCHEMA.url, URIRef(target)))


# ============================================================
# 6. READ XML
# ============================================================

if not XML_FILE.exists():
    raise FileNotFoundError(f"XML file not found: {XML_FILE.resolve()}")

parser = etree.XMLParser(remove_blank_text=False, recover=False)

try:
    tree = etree.parse(str(XML_FILE), parser)
except etree.XMLSyntaxError as error:
    raise RuntimeError(f"The XML is not well-formed:\n{error}") from error

root = tree.getroot()

uri_by_xml_id: dict[str, URIRef] = {}


# ============================================================
# 7. PERSONS
# ============================================================

for person in root.xpath(
    "//tei:profileDesc//tei:listPerson/tei:person",
    namespaces=NS,
):
    xml_id = get_xml_id(person)
    subject = get_project_uri(person)

    if xml_id:
        uri_by_xml_id[xml_id] = subject

    graph.add((subject, RDF.type, CRM.E21_Person))
    graph.add((subject, RDF.type, FOAF.Person))

    add_label(subject, get_text(person, "./tei:persName"))

    occupation = get_text(person, "./tei:occupation")
    if occupation:
        graph.add(
            (
                subject,
                SCHEMA.jobTitle,
                Literal(occupation, lang="en"),
            )
        )

    add_authority_links(person, subject)


# ============================================================
# 8. PLACES / BUILDINGS / MUSEUM
# ============================================================

for place in root.xpath(
    "//tei:profileDesc//tei:listPlace/tei:place",
    namespaces=NS,
):
    xml_id = get_xml_id(place)
    subject = get_project_uri(place)

    if xml_id:
        uri_by_xml_id[xml_id] = subject

    place_type = place.get("type", "")

    if place_type == "museum":
        graph.add((subject, RDF.type, CRM.E24_Physical_Human_Made_Thing))
        graph.add((subject, RDF.type, SCHEMA.Museum))
    elif place_type == "building":
        graph.add((subject, RDF.type, CRM.E24_Physical_Human_Made_Thing))
        graph.add(
            (
                subject,
                RDF.type,
                SCHEMA.LandmarksOrHistoricalBuildings,
            )
        )
    else:
        graph.add((subject, RDF.type, CRM.E53_Place))
        graph.add((subject, RDF.type, SCHEMA.Place))

    add_label(subject, get_text(place, "./tei:placeName"))

    function_description = get_text(
        place,
        './tei:state[@type="function"]/tei:desc',
    )

    if function_description:
        graph.add(
            (
                subject,
                EX.historicalFunction,
                Literal(function_description, lang="en"),
            )
        )

    add_authority_links(place, subject)


# ============================================================
# 9. ORGANIZATIONS
# ============================================================

for organization in root.xpath(
    "//tei:profileDesc/tei:listOrg/tei:org",
    namespaces=NS,
):
    xml_id = get_xml_id(organization)
    subject = get_project_uri(organization)

    if xml_id:
        uri_by_xml_id[xml_id] = subject

    graph.add((subject, RDF.type, CRM.E74_Group))
    graph.add((subject, RDF.type, SCHEMA.Organization))

    add_label(subject, get_text(organization, "./tei:orgName"))
    add_description(subject, get_text(organization, "./tei:note"))
    add_authority_links(organization, subject)
    add_urls(organization, subject)


# ============================================================
# 10. EVENTS
# ============================================================

for event in root.xpath(
    "//tei:profileDesc/tei:listEvent/tei:event",
    namespaces=NS,
):
    xml_id = get_xml_id(event)
    subject = get_project_uri(event)

    if xml_id:
        uri_by_xml_id[xml_id] = subject

    graph.add((subject, RDF.type, CRM.E5_Event))

    if event.get("type") == "adaptiveReuse":
        graph.add((subject, RDF.type, CRM.E11_Modification))

    add_label(subject, get_text(event, "./tei:label"))
    add_description(subject, get_text(event, "./tei:desc"))
    add_dates(event, subject)
    add_authority_links(event, subject)


# ============================================================
# 11. CONCEPTS
# ============================================================

for concept in root.xpath(
    "//tei:profileDesc/tei:textClass/tei:keywords/tei:term[@xml:id]",
    namespaces=NS,
):
    xml_id = get_xml_id(concept)
    subject = get_project_uri(concept)

    if xml_id:
        uri_by_xml_id[xml_id] = subject

    graph.add((subject, RDF.type, SKOS.Concept))

    label = get_text(concept, "./tei:term")
    if label:
        graph.add((subject, SKOS.prefLabel, Literal(label, lang="en")))

    add_description(subject, get_text(concept, "./tei:note"))
    add_authority_links(concept, subject, concept=True)


# ============================================================
# 12. BIBLIOGRAPHIC / DIGITAL RESOURCES
# ============================================================

for item in root.xpath(
    "//tei:standOff/tei:listBibl/tei:bibl",
    namespaces=NS,
):
    xml_id = get_xml_id(item)
    subject = get_project_uri(item)

    if xml_id:
        uri_by_xml_id[xml_id] = subject

    graph.add((subject, RDF.type, CRM.E73_Information_Object))

    item_type = item.get("type", "")

    if item_type == "digitalResource":
        graph.add((subject, RDF.type, SCHEMA.WebSite))
    elif item_type == "documentary":
        graph.add((subject, RDF.type, SCHEMA.Movie))
    else:
        graph.add((subject, RDF.type, SCHEMA.CreativeWork))

    title = get_text(item, "./tei:title")
    if title:
        graph.add((subject, DCTERMS.title, Literal(title, lang="en")))

    add_dates(item, subject)
    add_urls(item, subject)

    abstract = get_text(item, "./tei:abstract")
    if abstract:
        add_description(subject, abstract)

    series = get_text(item, './tei:note[@type="series"]')
    if series:
        graph.add((subject, SCHEMA.isPartOf, Literal(series, lang="en")))

    country = get_text(item, "./tei:country")
    if country:
        graph.add(
            (
                subject,
                SCHEMA.countryOfOrigin,
                Literal(country, lang="en"),
            )
        )

    duration = item.xpath(
        "./tei:extent/tei:measure[@unit='minute']/@quantity",
        namespaces=NS,
    )

    if duration:
        graph.add(
            (
                subject,
                SCHEMA.duration,
                Literal(
                    f"PT{duration[0]}M",
                    datatype=XSD.duration,
                ),
            )
        )


# ============================================================
# 13. RELATION MAPPING
# ============================================================

RELATION_MAP = {
    "designedBy": EX.designedBy,
    "openedFor": EX.openedFor,
    "hasArchitecturalStyle": EX.hasArchitecturalStyle,
    "wasModifiedBy": EX.wasModifiedBy,
    "resultedIn": EX.resultedIn,
    "samePhysicalBuildingDifferentFunction":
        EX.samePhysicalBuildingDifferentFunction,
    "interiorDesignedBy": EX.interiorDesignedBy,
    "housesWorksBy": EX.housesWorksBy,
    "representsArtMovement": EX.representsArtMovement,
    "isCaseOf": EX.isCaseOf,
    "representedIn": DCTERMS.isReferencedBy,
    "producedBy": SCHEMA.productionCompany,
    "digitallyRepresentedBy": EX.digitallyRepresentedBy,
    "providedBy": DCTERMS.publisher,
    "referencedIn": DCTERMS.isReferencedBy,
    "publishedBy": DCTERMS.publisher,
    "discussesConcept": DCTERMS.subject,
}


# ============================================================
# 14. LISTRELATION → RDF
# ============================================================

for relation in root.xpath(
    "//tei:standOff/tei:listRelation/tei:relation",
    namespaces=NS,
):
    name = relation.get("name")

    if not name:
        continue

    predicate = RELATION_MAP.get(name, EX[name])

    active_ids = [
        value.lstrip("#")
        for value in relation.get("active", "").split()
    ]

    passive_ids = [
        value.lstrip("#")
        for value in relation.get("passive", "").split()
    ]

    for active_id in active_ids:
        active_uri = uri_by_xml_id.get(active_id)

        if active_uri is None:
            print(f"Warning: active entity not found: {active_id}")
            continue

        for passive_id in passive_ids:
            passive_uri = uri_by_xml_id.get(passive_id)

            if passive_uri is None:
                print(f"Warning: passive entity not found: {passive_id}")
                continue

            graph.add((active_uri, predicate, passive_uri))


# ============================================================
# 15. CUSTOM PROPERTY DEFINITIONS
# ============================================================

custom_properties = {
    EX.designedBy: "designed by",
    EX.openedFor: "opened for",
    EX.hasArchitecturalStyle: "has architectural style",
    EX.wasModifiedBy: "was modified by",
    EX.resultedIn: "resulted in",
    EX.samePhysicalBuildingDifferentFunction:
        "same physical building, different function",
    EX.interiorDesignedBy: "interior designed by",
    EX.housesWorksBy: "houses works by",
    EX.representsArtMovement: "represents art movement",
    EX.isCaseOf: "is case of",
    EX.digitallyRepresentedBy: "digitally represented by",
    EX.historicalFunction: "historical function",
}

for property_uri, label in custom_properties.items():
    graph.add((property_uri, RDF.type, RDF.Property))
    graph.add((property_uri, RDFS.label, Literal(label, lang="en")))

graph.add((EX.designedBy, RDFS.subPropertyOf, DCTERMS.creator))
graph.add((EX.interiorDesignedBy, RDFS.subPropertyOf, DCTERMS.creator))
graph.add((EX.hasArchitecturalStyle, RDFS.range, SKOS.Concept))
graph.add((EX.representsArtMovement, RDFS.range, SKOS.Concept))
graph.add((EX.isCaseOf, RDFS.range, SKOS.Concept))

graph.add(
    (
        EX.samePhysicalBuildingDifferentFunction,
        RDFS.comment,
        Literal(
            "Relates distinct historical identities or functions of the same "
            "physical building and does not imply owl:sameAs.",
            lang="en",
        ),
    )
)


# ============================================================
# 16. SAVE
# ============================================================

graph.serialize(
    destination=str(OUTPUT_FILE),
    format="turtle",
    encoding="utf-8",
)

print("=" * 60)
print("TEI → RDF conversion completed")
print("=" * 60)
print(f"Input XML: {XML_FILE.resolve()}")
print(f"Output RDF: {OUTPUT_FILE.resolve()}")
print(f"Entities: {len(uri_by_xml_id)}")
print(f"Triples: {len(graph)}")
print("=" * 60)