#!/usr/bin/env python3
"""
csv_to_model.py
================
Transforms a triple-table CSV (source, predicate, target, source_type,
target_type, relation_type, description) into a self-contained interactive
HTML mind-map / Graffoo-style diagram, in the same visual style used across
the Musée d'Orsay LOD site (theoretical_model.html / conceptual_model.html).

Usage:
    python3 generate_model.py input.csv output.html "Page Title" "Subtitle text"

The layout is computed automatically (radial tree layout from the central
topic node), so re-running this script after editing the CSV regenerates a
consistent, up-to-date diagram without any manual coordinate work.
"""

import csv
import json
import math
import sys
import textwrap
import networkx as nx


# ---------------------------------------------------------------------------
# Visual configuration
# ---------------------------------------------------------------------------

# Node fill/stroke colours by entity type. Anything not listed here falls
# back to a deterministic hash-based colour, so new types added later still
# render sensibly without editing this script.
TYPE_COLORS = {
    "Topic":                     ("#25003c", "#130020"),
    "Building":                  ("#0f426c", "#082a45"),
    "Museum":                    ("#0f426c", "#082a45"),
    "Place":                     ("#0f426c", "#082a45"),
    "Transformation event":      ("#4e2e79", "#2f194a"),
    "Event":                     ("#4e2e79", "#2f194a"),
    "Concept":                   ("#315b43", "#1d3828"),
    "Person":                    ("#9b4f27", "#633219"),
    "Documentary":               ("#6a4a8d", "#402b59"),
    "Digital resource":          ("#6a4a8d", "#402b59"),
    "Reference":                 ("#6a4a8d", "#402b59"),
    "Organization":              ("#98622e", "#633d1c"),
    "Literal":                   ("#8a8378", "#5b564c"),
    "Authority record":          ("#2f70a6", "#1e4b72"),
    "Authority concept":         ("#2f70a6", "#1e4b72"),
    # Conceptual-model (OWL/Graffoo) types
    "Class":                     ("#a8792a", "#6b4f19"),
    "Datatype":                  ("#8a8378", "#5b564c"),
    "Vocabulary":                ("#5f6670", "#3c4147"),
    "Project property":          ("#3d6d8c", "#274859"),
    "Property":                  ("#3d6d8c", "#274859"),
    "OWL class":                 ("#6b4f96", "#43315f"),
    "External authority class":  ("#2f70a6", "#1e4b72"),
    "External authority concept":("#2f70a6", "#1e4b72"),
}

# Node radius by BFS depth from the central topic node (depth -> px)
RADIUS_BY_DEPTH = {0: 64, 1: 40, 2: 32, 3: 26}
DEFAULT_RADIUS = 19

# Angular ring spacing by depth (depth -> px from centre)
RING_BY_DEPTH = {0: 0, 1: 250, 2: 460, 3: 660}
RING_STEP_BEYOND = 180  # for depths deeper than defined above

# relation_type -> edge CSS class
PRIMARY_RELS = {"primary"}
AUTHORITY_RELS = {"authority", "authority mapping", "vocabulary reuse"}
SUPPORT_RELS = {
    "publisher", "production", "subject", "reference", "representation",
    "metadata", "collection", "classification", "conceptual",
}


def fallback_color(key):
    h = abs(hash(key)) % (256 ** 3)
    r, g, b = (h >> 16) & 255, (h >> 8) & 255, h & 255
    fill = f"#{r:02x}{g:02x}{b:02x}"
    stroke = f"#{r//2:02x}{g//2:02x}{b//2:02x}"
    return fill, stroke


def edge_class(relation_type):
    rt = (relation_type or "").strip().lower()
    if rt in PRIMARY_RELS:
        return "primary"
    if rt in AUTHORITY_RELS:
        return "authority"
    if rt in SUPPORT_RELS:
        return "support"
    return ""


def slugify(label):
    s = "".join(c.lower() if c.isalnum() else "_" for c in label)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")[:40] or "n"


def wrap_label(label, max_chars=11):
    return textwrap.wrap(label, max_chars, break_long_words=False) or [label]


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row for row in reader if row.get("source") and row.get("target")]


def build_graph(rows):
    nodes = {}   # id -> dict(label, type, description)
    edges = []   # list of dict(source, target, label, relation_type)

    def ensure_node(label, entity_type):
        nid = slugify(label)
        base = nid
        i = 1
        while nid in nodes and nodes[nid]["label"] != label:
            i += 1
            nid = f"{base}_{i}"
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "type": entity_type or "Entity", "description": ""}
        return nid

    for row in rows:
        sid = ensure_node(row["source"].strip(), row.get("source_type", "").strip())
        tid = ensure_node(row["target"].strip(), row.get("target_type", "").strip())
        desc = (row.get("description") or "").strip()
        if desc:
            # attach description to whichever endpoint doesn't have one yet
            if not nodes[tid]["description"]:
                nodes[tid]["description"] = desc
            elif not nodes[sid]["description"]:
                nodes[sid]["description"] = desc
        edges.append({
            "source": sid, "target": tid,
            "label": row["predicate"].strip(),
            "relation_type": (row.get("relation_type") or "").strip(),
        })

    return nodes, edges


def find_central(nodes, G):
    for nid, n in nodes.items():
        if n["type"].strip().lower() == "topic":
            return nid
    return max(G.degree, key=lambda kv: kv[1])[0]


def _radial_subdivide(tree, root):
    """Assign each node in a BFS tree an angular slot in [0, 2*pi),
    proportional to its subtree's leaf count (keeps sibling clusters
    grouped together, minimising edge crossings)."""
    leaf_count_cache = {}

    def leaf_count(n):
        if n in leaf_count_cache:
            return leaf_count_cache[n]
        children = list(tree.successors(n))
        val = 1 if not children else sum(leaf_count(c) for c in children)
        leaf_count_cache[n] = val
        return val

    angle = {}

    def assign(n, start, end):
        angle[n] = (start + end) / 2
        children = list(tree.successors(n))
        if not children:
            return
        total = sum(leaf_count(c) for c in children)
        cur = start
        for c in sorted(children, key=leaf_count, reverse=True):
            frac = leaf_count(c) / total
            width = (end - start) * frac
            assign(c, cur, cur + width)
            cur += width

    assign(root, 0.0, 2 * math.pi)
    return angle, leaf_count


def radial_layout(nodes, edges, central):
    """Radial-tree layout from the central topic node. The graph is not
    always fully connected (a CSV may describe a property both as an edge
    label *and* as its own node, e.g. for 'rdf:type'/'defined in' rows),
    so any node unreachable from the centre is placed in its own outer
    satellite cluster instead of being pushed further and further out."""
    G = nx.Graph()
    G.add_nodes_from(nodes.keys())
    for e in edges:
        G.add_edge(e["source"], e["target"])

    main_depth = nx.single_source_shortest_path_length(G, central)
    main_tree = nx.bfs_tree(G, central)
    main_angle, _ = _radial_subdivide(main_tree, central)
    max_depth = max(main_depth.values())

    pos = {}
    depth = dict(main_depth)

    def ring_radius(d):
        if d in RING_BY_DEPTH:
            return RING_BY_DEPTH[d]
        base_d = max(RING_BY_DEPTH)
        return RING_BY_DEPTH[base_d] + RING_STEP_BEYOND * (d - base_d)

    for nid in main_depth:
        d = main_depth[nid]
        r = ring_radius(d)
        a = main_angle.get(nid, 0.0)
        pos[nid] = (r * math.cos(a), r * math.sin(a))

    # --- satellite clusters: nodes not reachable from the central node ---
    orphan_nodes = [n for n in nodes if n not in main_depth]
    if orphan_nodes:
        components = [c for c in nx.connected_components(G) if central not in c]
        components.sort(key=len, reverse=True)
        total = sum(len(c) for c in components) or 1
        satellite_ring = ring_radius(max_depth) + RING_STEP_BEYOND
        cur_angle = 0.0
        for comp in components:
            wedge = 2 * math.pi * (len(comp) / total)
            subG = G.subgraph(comp)
            local_root = max(comp, key=lambda n: subG.degree(n))
            local_tree = nx.bfs_tree(subG, local_root)
            local_depth = nx.single_source_shortest_path_length(subG, local_root)
            local_angle, _ = _radial_subdivide(local_tree, local_root)
            for n in comp:
                d_local = local_depth.get(n, 0)
                r = satellite_ring + d_local * 140
                # map this node's local angle (0..2*pi) into our wedge
                a = cur_angle + (local_angle.get(n, 0.0) / (2 * math.pi)) * wedge
                pos[n] = (r * math.cos(a), r * math.sin(a))
                depth[n] = max_depth + 1 + d_local
            cur_angle += wedge

    return pos, depth, max(depth.values())


def build_svg_and_data(nodes, edges, central, canvas_pad=140):
    pos, depth, max_depth = radial_layout(nodes, edges, central)

    max_r = max(math.hypot(x, y) for x, y in pos.values()) if pos else 0
    half = max_r + canvas_pad
    cx, cy = half, half
    width = height = 2 * half

    def node_radius(nid):
        return RADIUS_BY_DEPTH.get(depth[nid], DEFAULT_RADIUS)

    def node_color(entity_type):
        return TYPE_COLORS.get(entity_type) or fallback_color(entity_type)

    svg_edges = []
    edge_records = []
    for i, e in enumerate(edges):
        sx, sy = pos[e["source"]]
        tx, ty = pos[e["target"]]
        cls = edge_class(e["relation_type"])
        svg_edges.append(
            f'<line id="edge-{i}" class="edge {cls}" data-source="{e["source"]}" '
            f'data-target="{e["target"]}" x1="{cx+sx:.1f}" y1="{cy+sy:.1f}" '
            f'x2="{cx+tx:.1f}" y2="{cy+ty:.1f}"/>'
        )
        edge_records.append({
            "source": e["source"], "target": e["target"],
            "label": e["label"], "kind": cls or "default",
        })

    svg_nodes = []
    node_data = {}
    for nid, n in nodes.items():
        x, y = pos[nid]
        px, py = cx + x, cy + y
        r = node_radius(nid)
        fill, stroke = node_color(n["type"])
        lines = wrap_label(n["label"])
        y0 = py - (len(lines) - 1) * 4.7
        tspans = "".join(
            f'<tspan x="{px:.1f}" dy="{0 if i==0 else 9.4}">{escape_xml(line)}</tspan>'
            for i, line in enumerate(lines)
        )
        svg_nodes.append(
            f'<g id="node-{nid}" class="node" data-id="{nid}">'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{fill}" stroke="{stroke}"/>'
            f'<text x="{px:.1f}" y="{y0:.1f}">{tspans}</text></g>'
        )
        node_data[nid] = {
            "id": nid, "label": n["label"], "type": n["type"],
            "description": n["description"] or n["label"],
        }

    svg = (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" aria-label="Model diagram">'
        + "".join(svg_edges) + "".join(svg_nodes) + "</svg>"
    )
    return svg, node_data, edge_records


def escape_xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


PAGE_TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
*{{box-sizing:border-box}}
html,body{{margin:0;background:#f3efe7;color:#2c241e;font-family:Arial,sans-serif}}
body{{padding:18px}}
.header{{max-width:1750px;margin:0 auto 10px}}
h1{{font-family:Georgia,serif;font-weight:500;font-size:25px;margin:0 0 4px}}
.subtitle{{font-size:12px;color:#776e65}}
.canvas{{max-width:1750px;margin:auto;overflow:auto;background:#f3efe7}}
svg{{display:block;width:100%;min-width:1500px;height:auto}}
.edge{{stroke:#cac1b8;stroke-width:1;opacity:.48;transition:.18s}}
.edge.primary{{stroke:#76549a;stroke-width:1.35;opacity:.66}}
.edge.authority{{stroke:#a6a09a;stroke-dasharray:4 5}}
.edge.support{{stroke:#927155;opacity:.5}}
.edge.active{{stroke:#6f4a94;stroke-width:2.2;opacity:1}}
.edge.dim{{opacity:.08}}
.node{{cursor:pointer;transition:.18s}}
.node circle{{stroke-width:2;transition:.18s}}
.node text{{fill:#fff;text-anchor:middle;font-size:8px;font-weight:600;pointer-events:none}}
.node.active circle{{filter:drop-shadow(0 0 8px rgba(76,43,111,.45));stroke-width:4}}
.node.dim{{opacity:.16}}
.tooltip{{
 position:fixed;z-index:50;display:none;pointer-events:none;
 width:min(360px,calc(100vw - 32px));padding:13px 15px;
 background:rgba(29,24,20,.96);color:#fff;border-radius:10px;
 box-shadow:0 10px 30px rgba(0,0,0,.22);font-size:12px;line-height:1.45
}}
.tooltip.show{{display:block}}
.tooltip .tt-title{{font-family:Georgia,serif;font-size:17px;margin-bottom:3px}}
.tooltip .tt-type{{color:#d4b8eb;font-size:10px;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}}
.tooltip .tt-desc{{color:#eee7df}}
.tooltip .tt-links{{margin-top:9px;padding-top:8px;border-top:1px solid rgba(255,255,255,.15);color:#d6cec6}}
.legend{{max-width:1750px;margin:9px auto 0;color:#746b62;font-size:10px}}
</style></head><body>
<div class="header"><h1>{title}</h1><div class="subtitle">{subtitle}</div></div>
<div class="canvas">{svg}</div>
<div class="legend">{legend}</div>
<div class="tooltip"></div><script>
const nodeData = {node_data_json};
const links = {links_json};
const tooltip = document.querySelector('.tooltip');
const nodeEls = [...document.querySelectorAll('.node')];
const edgeEls = [...document.querySelectorAll('.edge')];

function connected(id) {{
  const ids = new Set([id]);
  const rels = [];
  links.forEach((l,i) => {{
    if (l.source === id || l.target === id) {{
      ids.add(l.source); ids.add(l.target);
      const other = l.source === id ? l.target : l.source;
      const direction = l.source === id ? '\\u2192' : '\\u2190';
      rels.push(`${{direction}} ${{l.label}} \\u00b7 ${{nodeData[other].label}}`);
    }}
  }});
  return {{ids, rels}};
}}

function showNode(e,id) {{
  const d=nodeData[id];
  const c=connected(id);
  nodeEls.forEach(el => {{
    const eid=el.dataset.id;
    el.classList.toggle('active',eid===id);
    el.classList.toggle('dim',!c.ids.has(eid));
  }});
  edgeEls.forEach((el,i) => {{
    const l=links[i];
    const active=l.source===id || l.target===id;
    el.classList.toggle('active',active);
    el.classList.toggle('dim',!active);
  }});
  tooltip.innerHTML =
    `<div class="tt-title">${{d.label}}</div>`+
    `<div class="tt-type">${{d.type}}</div>`+
    `<div class="tt-desc">${{d.description}}</div>`+
    (c.rels.length ? `<div class="tt-links">${{c.rels.join('<br>')}}</div>` : '');
  tooltip.classList.add('show');
  moveTooltip(e);
}}

function moveTooltip(e) {{
  const pad=16;
  let x=e.clientX+18, y=e.clientY+18;
  const rect=tooltip.getBoundingClientRect();
  if(x+rect.width>window.innerWidth-pad) x=e.clientX-rect.width-18;
  if(y+rect.height>window.innerHeight-pad) y=e.clientY-rect.height-18;
  tooltip.style.left=Math.max(pad,x)+'px';
  tooltip.style.top=Math.max(pad,y)+'px';
}}

function clearAll() {{
  nodeEls.forEach(el=>el.classList.remove('active','dim'));
  edgeEls.forEach(el=>el.classList.remove('active','dim'));
  tooltip.classList.remove('show');
}}

nodeEls.forEach(el => {{
  const id=el.dataset.id;
  el.addEventListener('mouseenter',e=>showNode(e,id));
  el.addEventListener('mousemove',moveTooltip);
  el.addEventListener('mouseleave',clearAll);
}});
</script>
</body></html>
"""


def build_legend(nodes, edges):
    seen_types = {}
    for n in nodes.values():
        if n["type"] not in seen_types:
            seen_types[n["type"]] = TYPE_COLORS.get(n["type"]) or fallback_color(n["type"])
    items = "".join(
        f'<span class="item" style="margin-right:14px">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{color[0]};margin-right:5px;vertical-align:middle"></span>{t}</span>'
        for t, color in seen_types.items()
    )
    kinds_present = {edge_class(e["relation_type"]) or "default" for e in edges}
    kind_note = []
    if "primary" in kinds_present:
        kind_note.append("bold purple = primary relation")
    if "authority" in kinds_present:
        kind_note.append("dashed grey = authority / vocabulary link")
    if "support" in kinds_present:
        kind_note.append("brown = supporting / provenance relation")
    note = " &nbsp;\u00b7&nbsp; ".join(kind_note)
    return f'{items}<div style="margin-top:6px">{note}</div>'


def generate(csv_path, out_path, title, subtitle):
    rows = read_csv_rows(csv_path)
    nodes, edges = build_graph(rows)

    G = nx.Graph()
    G.add_nodes_from(nodes.keys())
    for e in edges:
        G.add_edge(e["source"], e["target"])
    central = find_central(nodes, G)

    svg, node_data, edge_records = build_svg_and_data(nodes, edges, central)
    legend = build_legend(nodes, edges)

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
    csv_path, out_path, title, subtitle = sys.argv[1:5]
    generate(csv_path, out_path, title, subtitle)