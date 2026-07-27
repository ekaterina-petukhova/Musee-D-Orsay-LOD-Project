import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

TEI_FILE = "tei.xml"
OUTPUT_FILE = "tei.html"

NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def get_xml_id(element):
    return element.attrib.get("{http://www.w3.org/XML/1998/namespace}id")


def normalize(text):
    if text is None:
        return ""
    return " ".join(text.split())


def collect_labels(root):
    labels = {}

    for person in root.findall(".//tei:listPerson/tei:person", NS):
        xml_id = get_xml_id(person)
        name = person.findtext("tei:persName", default="", namespaces=NS)
        occupation = person.findtext("tei:occupation", default="", namespaces=NS)

        if xml_id:
            label = f"Person: {normalize(name)}"
            if occupation:
                label += f" — {normalize(occupation)}"
            labels[xml_id] = label

    for place in root.findall(".//tei:listPlace/tei:place", NS):
        xml_id = get_xml_id(place)
        place_name = place.find("tei:placeName", NS)
        name = normalize("".join(place_name.itertext())) if place_name is not None else ""
        place_type = place.attrib.get("type", "place").capitalize()

        if xml_id:
            labels[xml_id] = f"{place_type}: {name}"

    for org in root.findall(".//tei:listOrg/tei:org", NS):
        xml_id = get_xml_id(org)
        org_name = org.find("tei:orgName", NS)
        name = normalize("".join(org_name.itertext())) if org_name is not None else ""

        if xml_id:
            labels[xml_id] = f"Organisation: {name}"

    for event in root.findall(".//tei:listEvent/tei:event", NS):
        xml_id = get_xml_id(event)
        label_el = event.find("tei:label", NS)
        label = normalize("".join(label_el.itertext())) if label_el is not None else ""

        if xml_id:
            labels[xml_id] = f"Event: {label}"

    for term in root.findall(".//tei:textClass/tei:keywords/tei:term", NS):
        xml_id = get_xml_id(term)
        label = normalize(term.text or "")

        if xml_id:
            labels[xml_id] = f"Concept: {label}"

    for bibl in root.findall(".//tei:listBibl/tei:bibl", NS):
        xml_id = get_xml_id(bibl)
        title_el = bibl.find("tei:title", NS)
        title = normalize("".join(title_el.itertext())) if title_el is not None else ""
        bibl_type = bibl.attrib.get("type", "resource").capitalize()

        if xml_id:
            labels[xml_id] = f"{bibl_type}: {title}"

    return labels


def ref_title(ref, labels):
    if not ref:
        return ""
    ref_id = ref.replace("#", "")
    return labels.get(ref_id, ref_id)


def render_inline(element, labels):
    output = escape(element.text or "")

    for child in list(element):
        tag = child.tag.split("}", 1)[-1]
        content = render_inline(child, labels)

        if tag == "persName":
            title = escape(ref_title(child.attrib.get("ref"), labels))
            html = f'<span class="persName" title="{title}">{content}</span>'

        elif tag == "placeName":
            title = escape(ref_title(child.attrib.get("ref"), labels))
            html = f'<span class="placeName" title="{title}">{content}</span>'

        elif tag == "orgName":
            title = escape(ref_title(child.attrib.get("ref"), labels))
            html = f'<span class="orgName" title="{title}">{content}</span>'

        elif tag == "term":
            title = escape(ref_title(child.attrib.get("ref"), labels))
            html = f'<span class="term" title="{title}">{content}</span>'

        elif tag == "date":
            when = escape(
                child.attrib.get("when")
                or child.attrib.get("from")
                or child.attrib.get("to")
                or ""
            )
            html = f'<span class="date" title="{when}">{content}</span>'

        elif tag == "quote":
            html = f'<q class="quote">{content}</q>'

        elif tag == "rs":
            rs_type = child.attrib.get("type", "entity")
            title = escape(ref_title(child.attrib.get("ref"), labels))
            html = f'<span class="{rs_type}" title="{title}">{content}</span>'

        elif tag == "title":
            html = f"<em>{content}</em>"

        else:
            html = content

        output += html + escape(child.tail or "")

    return output


def transform():
    tree = ET.parse(TEI_FILE)
    root = tree.getroot()
    labels = collect_labels(root)

    main_title = root.findtext(
        ".//tei:titleStmt/tei:title",
        default="TEI Document",
        namespaces=NS
    )

    subtitle = root.findtext(
        ".//tei:titleStmt/tei:subtitle",
        default="",
        namespaces=NS
    )

    paragraphs = []
    for p in root.findall(".//tei:text/tei:body//tei:p", NS):
        paragraphs.append("<p>" + render_inline(p, labels) + "</p>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{escape(main_title)} - TEI Edition</title>

<style>
body {{
    font-family: Georgia, serif;
    max-width: 900px;
    margin: 40px auto;
    padding: 0 22px;
    line-height: 1.75;
    color: #1d1d1d;
    background: #faf9f6;
}}

h1 {{
    font-size: 2.1em;
    border-bottom: 2px solid #9c6b30;
    padding-bottom: 10px;
    margin-bottom: 0.2em;
}}

.subtitle {{
    color: #6e5a45;
    font-style: italic;
    margin-bottom: 2em;
}}

.legend {{
    background: #fff;
    border: 1px solid #ddd2c2;
    padding: 15px 20px;
    margin: 28px 0;
    border-radius: 6px;
    font-size: 0.92em;
}}

.legend span {{
    display: inline-block;
    margin-right: 16px;
    margin-bottom: 6px;
}}

.persName {{
    color: #8b0000;
    font-weight: bold;
    border-bottom: 1px dotted #8b0000;
}}

.placeName {{
    color: #004b7a;
    font-weight: bold;
    border-bottom: 1px dotted #004b7a;
}}

.orgName {{
    color: #5a3e91;
    font-weight: bold;
    border-bottom: 1px dotted #5a3e91;
}}

.event {{
    color: #2e6b2e;
    font-style: italic;
    border-bottom: 1px dotted #2e6b2e;
}}

.term {{
    color: #7a4000;
    font-weight: bold;
    border-bottom: 1px dotted #7a4000;
}}

.documentary,
.digitalResource {{
    color: #555;
    font-style: italic;
    border-bottom: 1px dotted #555;
}}

.date {{
    color: #6b4b00;
}}

.quote {{
    color: #333;
    background: #f1eadf;
    padding: 0 3px;
}}

.source {{
    font-size: 0.85em;
    color: #777;
    margin-top: 40px;
    border-top: 1px solid #ddd2c2;
    padding-top: 12px;
}}
</style>
</head>

<body>

<h1>{escape(main_title)}</h1>
<div class="subtitle">{escape(subtitle)}</div>

<div class="legend">
<strong>Annotation Legend:</strong><br>
<span class="persName">Person</span>
<span class="placeName">Place / Museum</span>
<span class="orgName">Organisation</span>
<span class="event">Event</span>
<span class="term">Concept</span>
<span class="documentary">Documentary</span>
<span class="digitalResource">Digital resource</span>
<span class="date">Date</span>
<q class="quote">Quotation</q>
</div>

{chr(10).join(paragraphs)}

<div class="source">
<p>Source: Wikipedia pages “Gare d’Orsay” and “Musée d’Orsay”.</p>
<p>TEI encoding and XML to HTML transformation: Ekaterina Petukhova - University of Bologna.</p>
</div>

</body>
</html>
"""

    Path(OUTPUT_FILE).write_text(html, encoding="utf-8")

    print(f"HTML output written to {OUTPUT_FILE}")


if __name__ == "__main__":
    transform()