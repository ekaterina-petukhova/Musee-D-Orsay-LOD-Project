#!/usr/bin/env python3
"""Non-network project integrity checks; not a substitute for schema/authority verification."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
from bs4 import BeautifulSoup
from lxml import etree
from rdflib import Graph
root=Path(__file__).resolve().parent
fails=[];warnings=[]
for path in root.rglob('*.html'):
 soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
 for el in soup.find_all(['a','img','script','link','iframe']):
  for attr in ('href','src'):
   url=el.get(attr)
   if not url or url.startswith(('#','data:','mailto:','tel:','javascript:')):continue
   parsed=urlsplit(url)
   if parsed.scheme or parsed.netloc or url.startswith('//'):continue
   pathpart=unquote(parsed.path)
   if not pathpart:continue
   resolved=(path.parent/pathpart).resolve()
   if not resolved.is_relative_to(root.resolve()):fails.append(f'Unsafe path: {path.relative_to(root)} -> {url}');continue
   if not resolved.is_file():
    kind='IMAGE' if el.name=='img' else 'LOCAL LINK'
    msg=f'{kind}: {path.relative_to(root)} -> {url}'
    (warnings if kind=='IMAGE' else fails).append(msg)
try:etree.parse(str(root/'data/tei.xml'));print('PASS XML well-formedness (not TEI schema)')
except Exception as e:fails.append('TEI parse: '+str(e))
for path in [root/'data/rdf.ttl',root/'diagrams/orsay_ontology.ttl',root/'data/rdf.jsonld']:
 try:
  fmt='json-ld' if path.suffix=='.jsonld' else 'turtle';g=Graph().parse(path,format=fmt);print(f'PASS {path.relative_to(root)}: {len(g)} triples')
 except Exception as e:fails.append(f'RDF {path.name}: {e}')
print(f'Missing image assets: {len(warnings)} (needs original licensed images)')
for x in warnings[:30]:print('WARNING',x)
for x in fails:print('FAIL',x)
print(f'CHECK RESULT: {len(fails)} failures, {len(warnings)} warnings')
raise SystemExit(bool(fails))
