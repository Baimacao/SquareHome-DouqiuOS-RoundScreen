#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
APK = r"E:\B1807\Documents\DSH\squarehome-mod\squarehome-orig.apk"
z = zipfile.ZipFile(APK)
infos = z.infolist()
print("total entries:", len(infos))
print("\n-- META-INF (all) --")
for i in infos:
    if i.filename.startswith("META-INF/"):
        print(f"  {i.filename}  method={i.compress_type} size={i.file_size}")
print("\n-- stored (method=0) --")
st = [i.filename for i in infos if i.compress_type == 0]
print("  count:", len(st))
for n in st[:20]:
    print("  ", n)
print("\n-- key entries --")
for i in infos:
    if i.filename in ("resources.arsc", "AndroidManifest.xml", "stamp-cert-sha256") or i.filename.startswith("classes"):
        print(f"  {i.filename}  method={i.compress_type} size={i.file_size} comp={i.compress_size}")
print("\n-- first 5 / last 5 names --")
print([i.filename for i in infos[:5]])
print([i.filename for i in infos[-5:]])
