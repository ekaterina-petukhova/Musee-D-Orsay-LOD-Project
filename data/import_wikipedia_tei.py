#!/usr/bin/env python3
"""Build a TEI edition from the actual Wikipedia Musée d’Orsay page.

Run on a connected computer: python data/import_wikipedia_tei.py
Install: python -m pip install requests beautifulsoup4 lxml rdflib

Default: preserves the existing entity records, relations and enrichment. Replaces
only the TEI text/body with verbatim source paragraphs selected from the specified
article (lead and History), annotated with links to existing TEI IDs.

It MUST be reviewed before submission: machine annotation finds mentions, it does
not verify every Wikidata/VIAF identifier or ensure that all metadata is accurate.
"""
from pathlib import Path
from copy import deepcopy
import re, requests
from bs4 import BeautifulSoup
from lxml import etree
from datetime import date

BASE=Path(__file__).resolve().parent
TEI=BASE/'tei.xml'
BACKUP=BASE/'tei_adapted_backup.xml'
URL='https://en.wikipedia.org/wiki/Mus%C3%A9e_d%27Orsay'
NS='http://www.tei-c.org/ns/1.0'
XML='http://www.w3.org/XML/1998/namespace'
q=lambda name:f'{{{NS}}}{name}'

# These strings are attested in the primary article's lead/History as of 19 Oct 2026.
# Longest-first deterministic match prevents shorter labels from swallowing others.
MENTIONS={
 'Musée d’Orsay':('placeName','museeOrsay'), 'Musée d\'Orsay':('placeName','museeOrsay'),
 'Gare d’Orsay':('placeName','gareOrsay'), 'Gare d\'Orsay':('placeName','gareOrsay'),
 'Victor Laloux':('persName','victorLaloux'), 'Gae Aulenti':('persName','gaeAulenti'),
 'Claude Monet':('persName','claudeMonet'), 'Cézanne':('persName','paulCezanne'),
 'Paul Cézanne':('persName','paulCezanne'),
 'Exposition Universelle':('rs','expo1900'),
 'Beaux-Arts':('term','beauxArtsStyle'),
 'Impressionist':('term','impressionism'), 'Impressionism':('term','impressionism'),
 'post-Impressionist':('term','postImpressionism'),
 'Post-Impressionist':('term','postImpressionism'),
}
pattern=re.compile('|'.join(re.escape(k) for k in sorted(MENTIONS,key=len,reverse=True)), re.I)
normalized={k.casefold():v for k,v in MENTIONS.items()}

def append_text(el,s):
 if len(el): el[-1].tail=(el[-1].tail or '')+s
 else: el.text=(el.text or '')+s

def annotate(p,text):
 start=0
 for m in pattern.finditer(text):
  append_text(p,text[start:m.start()])
  tag,ref=normalized[m.group().casefold()]
  node=etree.SubElement(p,q(tag));node.set('ref','#'+ref)
  if tag=='rs':node.set('type','event')
  node.text=m.group();start=m.end()
 append_text(p,text[start:])

def select_paragraphs(page):
 soup=BeautifulSoup(page,'html.parser')
 content=soup.select_one('#mw-content-text .mw-parser-output') or soup.select_one('.mw-parser-output')
 if content is None:raise RuntimeError('Wikipedia page structure changed: no content container')
 paragraphs=[];in_history=False
 for el in content.children:
  if getattr(el,'name',None) in ('h2','section'):
   title=el.get_text(' ',strip=True).lower()
   if 'history' in title: in_history=True
   elif in_history and ('collection' in title or 'management' in title):break
  if getattr(el,'name',None)=='p':
   text=el.get_text(' ',strip=True)
   text=re.sub(r'\[\d+\]','',text)
   if len(text)>70: paragraphs.append(text)
   if len(paragraphs)>=12:break
 if len(paragraphs)<4:
  paragraphs=[]
  for p in content.find_all('p'):
   text=re.sub(r'\[\d+\]','',p.get_text(' ',strip=True))
   if len(text)>70: paragraphs.append(text)
   if len(paragraphs)>=12:break
 return paragraphs

def main():
 resp=requests.get(URL,timeout=25,headers={'User-Agent':'Musée-dOrsay-academic-TEI/1.0 (student project)'})
 resp.raise_for_status()
 paras=select_paragraphs(resp.text)
 if len(paras)<4:raise RuntimeError('Too few article paragraphs extracted; review Wikipedia markup')
 tree=etree.parse(str(TEI));base=tree.getroot()
 body=base.find('.//'+q('text')+'/'+q('body'))
 if body is None:raise RuntimeError('Missing TEI body')
 if not BACKUP.exists():BACKUP.write_bytes(TEI.read_bytes())
 for ch in list(body):body.remove(ch)
 div=etree.SubElement(body,q('div'),type='wikipedia-article')
 head=etree.SubElement(div,q('head'));head.text='Musée d’Orsay — Wikipedia article (selected sections)'
 for para in paras:
  p=etree.SubElement(div,q('p'));annotate(p,para)
 # Correct attribution/license for extracted Wikipedia text
 license_node=base.find('.//'+q('availability')+'/'+q('licence'))
 if license_node is not None:
  license_node.set('target','https://creativecommons.org/licenses/by-sa/4.0/')
  license_node.text='Wikipedia source text: CC BY-SA 4.0; TEI annotation and accompanying research separately authored'
 enc=base.find('.//'+q('encodingDesc')+'/'+q('projectDesc'))
 if enc is not None:
  for e in list(enc):
   if 'NOT a transcription' in ''.join(e.itertext()) or 'Source policy:' in ''.join(e.itertext()):enc.remove(e)
  p=etree.SubElement(enc,q('p'));p.text=('The running text consists of selected verbatim paragraphs from '+URL+' retrieved on '+date.today().isoformat()+'. The standOff bibliography and semantic relations may additionally model enriched entities not mentioned in these paragraphs. Source is attributed under CC BY-SA 4.0.')
 ids={e.get('{'+XML+'}id') for e in base.xpath('//*[@xml:id]',namespaces={'xml':XML})}
 refs=[e.get('ref','')[1:] for e in body.xpath('.//*[@ref]')]
 missing=set(refs)-ids
 if missing:raise RuntimeError('Unresolved references '+str(missing))
 if len(set(refs))<10:raise RuntimeError('Only '+str(len(set(refs)))+' entity IDs annotated; use additional relevant Wikipedia paragraphs')
 tree.write(str(TEI),encoding='utf-8',xml_declaration=True,pretty_print=True)
 print('Saved',TEI, 'paragraphs=',len(paras),'distinct annotated IDs=',len(set(refs)))
 print('Review the annotated source against '+URL)
if __name__=='__main__':main()
