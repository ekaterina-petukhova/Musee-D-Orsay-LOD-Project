#!/usr/bin/env python3
"""TEI source integrity checks and optional official P5 Relax NG validation.

Usage:
  python validate_tei.py
  python validate_tei.py /path/to/tei_all.rng

The first command does NOT establish conformance to TEI P5. The second does,
subject to the constraints of that selected official schema version.
"""
from pathlib import Path
from collections import Counter
import sys
from lxml import etree

root = Path(__file__).resolve().parent
path = root / 'data' / 'tei.xml'
NS = {'tei':'http://www.tei-c.org/ns/1.0','xml':'http://www.w3.org/XML/1998/namespace'}
XML_ID='{http://www.w3.org/XML/1998/namespace}id'
errors=[]
try:
    doc=etree.parse(str(path))
except (OSError,etree.XMLSyntaxError) as e:
    sys.exit(f'FAIL: XML parse: {e}')
if doc.getroot().tag!='{http://www.tei-c.org/ns/1.0}TEI':
    errors.append('Wrong root or TEI namespace')
for xpath in ['/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title',
              '/tei:TEI/tei:teiHeader/tei:fileDesc/tei:publicationStmt',
              '/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc',
              '/tei:TEI/tei:text/tei:body']:
    if not doc.xpath(xpath,namespaces=NS):errors.append('Missing required structure: '+xpath)
seen=Counter(n.get(XML_ID) for n in doc.xpath('//*[@xml:id]',namespaces=NS))
for val,count in seen.items():
    if count>1:errors.append(f'Duplicate xml:id: {val}')
ids=set(seen)
# TEI pointing attributes may be whitespace-separated lists of references.
for el in doc.iter():
    for attr,value in el.attrib.items():
        if etree.QName(attr).localname not in {'ref','target','corresp','ana','active','passive','mutual','who','sameAs','exclude'}:
            continue
        for token in value.split():
            if token.startswith('#') and token[1:] not in ids:
                errors.append(f'Unresolved {etree.QName(attr).localname} {token} at line {el.sourceline}')
print('XML well-formedness and project referential integrity:', 'PASS' if not errors else 'FAIL')
print(f'Identified xml:id nodes: {len(ids)}; TEI relations: {len(doc.xpath("//tei:relation",namespaces=NS))}')
for error in errors: print('ERROR:',error)
if len(sys.argv)>1:
    schema_path=Path(sys.argv[1])
    if not schema_path.exists():
        errors.append('Official schema file not found: '+str(schema_path))
    else:
        try:
            validator=etree.RelaxNG(etree.parse(str(schema_path)))
            valid=validator.validate(doc)
            print('TEI P5 Relax NG:', 'PASS' if valid else 'FAIL')
            if not valid:
                errors.append('Relax NG validation failed')
                for log in validator.error_log:print('SCHEMA:',log)
        except (etree.XMLSyntaxError,etree.RelaxNGParseError) as e:
            errors.append('Cannot load Relax NG schema: '+str(e))
else:
    print('TEI P5 Relax NG: NOT EXECUTED (official tei_all.rng not available locally)')
for error in errors:
    if error.startswith('Official schema') or error.startswith('Cannot load'):
        print('ERROR:',error)
raise SystemExit(1 if errors else 0)
