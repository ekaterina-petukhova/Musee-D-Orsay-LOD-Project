#!/usr/bin/env python3
"""Rebuild the HTML and RDF outputs after editing TEI.
Run: python rebuild.py [--import-wikipedia]
"""
from pathlib import Path
import subprocess,sys
base=Path(__file__).resolve().parent
steps=[]
if '--import-wikipedia' in sys.argv:steps.append(base/'data'/'import_wikipedia_tei.py')
steps += [base/'data'/'tei_to_rdf.py',base/'data'/'tei_to_html.py']
for script in steps:
 print('Running',script.relative_to(base),flush=True)
 subprocess.run([sys.executable,str(script)],cwd=base,check=True)
print('RDF and TEI HTML regenerated.')
