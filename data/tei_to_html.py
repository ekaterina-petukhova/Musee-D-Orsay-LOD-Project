from pathlib import Path
from html import escape
from lxml import etree

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "tei.xml"
TARGET = BASE.parent / "tei.html"
ns = {"tei": "http://www.tei-c.org/ns/1.0"}
root = etree.parse(str(SOURCE))
body = root.find(".//tei:text/tei:body", namespaces=ns)

def render(node):
    tag = etree.QName(node).localname
    content = escape(node.text or "")
    for child in node:
        content += render(child) + escape(child.tail or "")
    if tag in ("p", "div", "head", "title"):
        html_tag = {"head":"h2","title":"h3"}.get(tag,tag)
        return f"<{html_tag}>{content}</{html_tag}>"
    ref = node.get("ref")
    if ref:
        return f'<mark title="TEI reference: {escape(ref, quote=True)}">{content}</mark>'
    if tag == "date":
        return f'<time>{content}</time>'
    return content
html = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Musée d’Orsay — TEI Edition</title><style>body{font:17px/1.8 Georgia,serif;max-width:850px;margin:auto;padding:40px 24px;background:#faf8f4;color:#241d14}mark{background:#f2dfab;border-bottom:1px solid #a8792a;padding:0 2px}a{color:#8b601e}</style><p><a href="representation.html">← Knowledge Representation</a></p><h1>TEI-encoded text</h1><p>Highlighted phrases are linked to identified entities in the TEI source.</p>""" + render(body) + "</html>"
TARGET.write_text(html, encoding="utf-8")
print(TARGET)
