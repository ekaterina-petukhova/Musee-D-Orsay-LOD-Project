#!/usr/bin/env python3
"""
ttl_to_diagram.py
=================
Parses the actual RDF/Turtle knowledge graph (the populated data - "A-box",
as opposed to the CSV files which describe the theoretical/conceptual
*schema*) and renders it as a self-contained interactive HTML diagram, in
the same visual style as theoretical_model.html / conceptual_model.html.

Usage:
    python3 ttl_to_diagram.py input.ttl output.html "Page Title" "Subtitle text"
"""

import sys
import re
import rdflib
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS

from generate_model import (
    radial_layout, build_legend, PAGE_TEMPLATE, escape_xml, TYPE_COLORS,
    fallback_color, wrap_label, edge_class,
)
import generate_model as gm

SKOS_PREFLABEL = URIRef("http://www.w3.org/2004/02/skos/core#prefLabel")
SKOS_EXACTMATCH = URIRef("http://www.w3.org/2004/02/skos/core#exactMatch")
DCTERMS_TITLE = URIRef("http://purl.org/dc/terms/title")
DCTERMS_DESCRIPTION = URIRef("http://purl.org/dc/terms/description")
OWL_SAMEAS = URIRef("http://www.w3.org/2002/07/owl#sameAs")
OWL_PROPERTY_CLASSES = {URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Property")}

# Literal-valued predicates whose value we fold into the tooltip description
# rather than turning into a separate node/edge.
LITERAL_ONLY_PREDICATES_LOCAL = {
    "historicalFunction", "jobTitle", "isPartOf", "countryOfOrigin",
    "duration", "date", "startDate", "endDate", "url", "comment",
}

# rdf:type local name -> our display category (checked in priority order)
TYPE_PRIORITY = [
    ("Museum", "Museum"),
    ("LandmarksOrHistoricalBuildings", "Building"),
    ("E11_Modification", "Transformation event"),
    ("E5_Event", "Event"),
    ("Person", "Person"),
    ("Concept", "Concept"),
    ("Organization", "Organization"),
    ("E74_Group", "Organization"),
    ("Movie", "Documentary"),
    ("WebSite", "Digital resource"),
    ("CreativeWork", "Reference"),
    ("E73_Information_Object", "Reference"),
]

AUTHORITY_DOMAINS = [
    ("wikidata.org", "Wikidata"),
    ("viaf.org", "VIAF"),
    ("isni.org", "ISNI"),
    ("vocab.getty.edu/ulan", "Getty ULAN"),
    ("vocab.getty.edu/aat", "Getty AAT"),
    ("id.loc.gov", "LCSH"),
]


def local_name(uri):
    s = str(uri)
    s = re.split(r"[#/]", s)[-1]
    return s


def humanize(name):
    # camelCase -> spaced words, lowercase
    s = re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()
    return s


def is_instance(uri):
    return "/id/" in str(uri)


def authority_label(uri):
    s = str(uri)
    for domain, label in AUTHORITY_DOMAINS:
        if domain in s:
            return label
    return local_name(uri)


def node_type_from_rdf_types(rdf_types):
    names = {local_name(t) for t in rdf_types}
    for key, category in TYPE_PRIORITY:
        if key in names:
            return category
    return "Entity"


def parse_ttl(path):
    g = rdflib.Graph()
    g.parse(path, format="turtle")

    # property declarations: ex:foo a rdf:Property ; rdfs:label "..."
    prop_labels = {}
    for s, p, o in g.triples((None, RDF.type, None)):
        if o in OWL_PROPERTY_CLASSES:
            lbl = g.value(s, RDFS.label)
            if lbl:
                prop_labels[s] = str(lbl)

    def pred_label(pred):
        if pred in prop_labels:
            return prop_labels[pred]
        return humanize(local_name(pred))

    nodes = {}   # uri (str) -> dict(label, type, description)
    edges = []   # dict(source, target, label, relation_type)

    instance_subjects = {s for s in g.subjects() if isinstance(s, URIRef) and is_instance(s)}

    def ensure_node(uri):
        key = str(uri)
        if key not in nodes:
            nodes[key] = {"label": local_name(uri).replace("-", " ").title(),
                          "type": "Entity", "description": ""}
        return key

    for subj in instance_subjects:
        sid = ensure_node(subj)
        rdf_types = list(g.objects(subj, RDF.type))
        nodes[sid]["type"] = node_type_from_rdf_types(rdf_types)

        label = (g.value(subj, RDFS.label) or g.value(subj, SKOS_PREFLABEL)
                 or g.value(subj, DCTERMS_TITLE))
        if label:
            nodes[sid]["label"] = str(label)

        desc = g.value(subj, DCTERMS_DESCRIPTION)
        if desc:
            nodes[sid]["description"] = str(desc).strip()

        for pred, obj in g.predicate_objects(subj):
            if pred in (RDF.type, RDFS.label, SKOS_PREFLABEL, DCTERMS_TITLE, DCTERMS_DESCRIPTION):
                continue

            if isinstance(obj, Literal):
                pname = local_name(pred)
                if pname in LITERAL_ONLY_PREDICATES_LOCAL and not nodes[sid]["description"]:
                    nodes[sid]["description"] = str(obj).strip()
                continue

            if not isinstance(obj, URIRef):
                continue

            if pred in (OWL_SAMEAS, SKOS_EXACTMATCH):
                tid = str(obj)
                if tid not in nodes:
                    nodes[tid] = {
                        "label": authority_label(obj),
                        "type": "Authority concept" if pred == SKOS_EXACTMATCH else "Authority record",
                        "description": str(obj),
                    }
                edges.append({"source": sid, "target": tid,
                              "label": "same as" if pred == OWL_SAMEAS else "exact match",
                              "relation_type": "authority"})
                continue

            if is_instance(obj):
                tid = ensure_node(obj)
                edges.append({"source": sid, "target": tid,
                              "label": pred_label(pred), "relation_type": "object property"})
            # else: external, non-authority URI (e.g. schema:url handled as literal-like) -> skip

    # re-key nodes with short slug ids (radial_layout/build_svg_and_data expect hashable, short ids)
    id_map = {}
    for i, key in enumerate(nodes):
        id_map[key] = re.sub(r"[^a-z0-9]+", "_", local_name(key).lower())[:40] or f"n{i}"
    # ensure uniqueness
    seen = {}
    for key, slug in list(id_map.items()):
        base = slug
        n = 1
        while slug in seen and seen[slug] != key:
            n += 1
            slug = f"{base}_{n}"
        seen[slug] = key
        id_map[key] = slug

    final_nodes = {id_map[k]: v for k, v in nodes.items()}
    final_edges = [
        {"source": id_map[e["source"]], "target": id_map[e["target"]],
         "label": e["label"], "relation_type": e["relation_type"]}
        for e in edges
    ]
    return final_nodes, final_edges


def find_central(nodes, edges):
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(nodes.keys())
    for e in edges:
        G.add_edge(e["source"], e["target"])
    # prefer the node with the most connections among "Museum"/"Building" types
    candidates = [n for n, d in nodes.items() if d["type"] in ("Museum", "Building")]
    if candidates:
        return max(candidates, key=lambda n: G.degree(n))
    return max(G.degree, key=lambda kv: kv[1])[0]


def resolve_overlaps(pos, nodes, depth, central, iterations=300, margin=1.08):
    """Iteratively push apart any two nodes whose circles overlap. Keeps the
    central node fixed; everything else is nudged along the line connecting
    the overlapping pair. Cheap fix for locally dense neighbourhoods (e.g. a
    hub entity with many same-as authority links crowding one angular
    sector) without touching the shared radial-tree layout used by the
    CSV-based diagrams."""
    ids = list(pos.keys())

    def radius(nid):
        return gm.RADIUS_BY_DEPTH.get(depth[nid], gm.DEFAULT_RADIUS)

    pos = {k: list(v) for k, v in pos.items()}
    for _ in range(iterations):
        moved = False
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                ax, ay = pos[a]
                bx, by = pos[b]
                dx, dy = bx - ax, by - ay
                dist = (dx * dx + dy * dy) ** 0.5
                min_dist = (radius(a) + radius(b)) * margin
                if dist < min_dist:
                    moved = True
                    if dist < 1e-6:
                        dx, dy, dist = 1.0, 0.0, 1.0
                    push = (min_dist - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    if a != central:
                        pos[a][0] -= ux * push
                        pos[a][1] -= uy * push
                    if b != central:
                        pos[b][0] += ux * push
                        pos[b][1] += uy * push
        if not moved:
            break
    return {k: tuple(v) for k, v in pos.items()}


def generate(ttl_path, out_path, title, subtitle):
    nodes, edges = parse_ttl(ttl_path)
    central = find_central(nodes, edges)
    pos, depth, max_depth = radial_layout(nodes, edges, central)
    pos = resolve_overlaps(pos, nodes, depth, central)
    svg, node_data, edge_records = gm.build_svg_and_data_from_pos(nodes, edges, pos, depth)
    legend = build_legend(nodes, edges)

    import json
    html = PAGE_TEMPLATE.format(
        title=escape_xml(title),
        subtitle=escape_xml(subtitle),
        svg=svg,
        legend=legend,
        node_data_json=json.dumps(node_data, ensure_ascii=False),
        links_json=json.dumps(edge_records, ensure_ascii=False),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {out_path}  ({len(nodes)} nodes, {len(edges)} edges)")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)
    generate(*sys.argv[1:5])
