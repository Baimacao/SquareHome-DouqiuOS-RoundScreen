#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 组装：以 apktool 全量重编译产物为基底（含新资源/新 arsc/新 manifest），
   换入打过钩子的 classes.dex / classes2.dex / classes4.dex，
   classes3/5/6.dex 用原包（逐字节未改），去掉旧签名与 stamp。"""
import hashlib, io, os, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
BASE = os.path.join(W, "work3", "built-full.apk")          # apktool 全量重编译
OUT = os.path.join(W, "work3", "squarehome-v8-unsigned.apk")
PATCHED = {"classes.dex": os.path.join(W, "work3", "patched", "classes.dex"),
           "classes2.dex": os.path.join(W, "work3", "patched", "classes2.dex"),
           "classes4.dex": os.path.join(W, "work3", "patched", "classes4.dex")}
KEEP_ORIG = ("classes3.dex", "classes5.dex", "classes6.dex")
DROP = {"stamp-cert-sha256"}


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


base = zipfile.ZipFile(BASE)
orig = zipfile.ZipFile(ORIG)
new = {k: open(v, "rb").read() for k, v in PATCHED.items()}
new.update({k: orig.read(k) for k in KEEP_ORIG})
for k, v in new.items():
    print(f"  {k}: {len(v)} bytes sha={sha(v)}")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as dst:
    for info in base.infolist():
        n = info.filename
        if n in DROP or (n.startswith("META-INF/") and n.split(".")[-1] in ("MF", "SF", "RSA", "DSA", "EC")):
            print("  dropped", n)
            continue
        data = new.get(n)
        if data is None:
            data = base.read(n)
        zi = zipfile.ZipInfo(n, info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.internal_attr = info.internal_attr
        zi.create_system = info.create_system
        dst.writestr(zi, data, compress_type=info.compress_type)
base.close()

z = zipfile.ZipFile(OUT)
names = z.namelist()
print(f"\nout: {OUT} ({os.path.getsize(OUT)} bytes, {len(names)} entries)")
print("resources.arsc stored:", z.getinfo("resources.arsc").compress_type == 0,
      "| manifest:", z.getinfo("AndroidManifest.xml").file_size,
      "| arsc:", z.getinfo("resources.arsc").file_size)
for k in PATCHED:
    print(f"  {k} inside == patched:", hashlib.sha256(z.read(k)).hexdigest() == hashlib.sha256(new[k]).hexdigest())
for k in KEEP_ORIG:
    print(f"  {k} == original:", z.read(k) == orig.read(k))
# 与原包对比：哪些条目变了
ob = {i.filename: i for i in orig.infolist()}
nb = {i.filename: i for i in z.infolist()}
same = [n for n in ob if n in nb and orig.read(n) == z.read(n)]
print(f"entries identical to original: {len(same)} / {len(ob)}")
print("apk sha256:", hashlib.sha256(open(OUT, 'rb').read()).hexdigest())
