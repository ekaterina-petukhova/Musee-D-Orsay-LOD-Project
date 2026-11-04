#!/usr/bin/env python3
"""Copy missing, exact-named images from an original images folder. Never substitutes unrelated photographs."""
from pathlib import Path
import sys,re,shutil
base=Path(__file__).resolve().parent
if len(sys.argv)!=2:
 print('Usage: python restore_images.py /path/to/original-images');raise SystemExit(2)
source=Path(sys.argv[1]); dest=base/'images'
needed=set()
for file in base.glob('*.html'):
 needed.update(re.findall(r'images/([a-zA-Z0-9._-]+\.(?:jpg|jpeg|png|webp))',file.read_text()))
for name in sorted(needed):
 found=list(source.rglob(name)) if source.is_dir() else []
 if not found: print('MISSING:',name);continue
 shutil.copy2(found[0],dest/name);print('RESTORED:',name)
