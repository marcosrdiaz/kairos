"""Quita las entradas de carpeta del ZIP de un .pptx (pptxgenjs las escribe; molestan en la nube)."""

import shutil
import sys
import zipfile

src = sys.argv[1]
tmp = src + ".tmp"
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename.endswith("/"):
            continue
        zout.writestr(item, zin.read(item.filename))
shutil.move(tmp, src)
print("sin carpetas:", src)
