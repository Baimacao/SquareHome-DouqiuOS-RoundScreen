#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v9 组装：apktool 全量重编译产物为基底 + 打过钩子的 classes.dex/2.dex/4.dex，
   classes3/5/6.dex 用原包，去掉旧签名与 stamp。"""
import hashlib, io, os, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
BASE = os.path.join(W, "work3", "built-full.apk")
OUT = os.path.join(W, "work3", "squarehome-v9-unsigned.apk")
PATCHED = {"classes.dex": os.path.join(W, "work3", "patched", "classes.dex"),
           "classes2.dex": os.path.join(W, "work3", "patched", "classes2.dex"),
           "classes4.dex": os.path.join(W, "work3", "patched", "classes4.dex")}
KEEP_ORIG = ("classes3.dex", "classes5.dex", "classes6.dex")
DROP = {"stamp-cert-sha256"}

sha = lambda b: hashlib.sha256(b).hexdigest()[:16]
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
print(f"\nout: {OUT} ({os.path.getsize(OUT)} bytes, {len(z.namelist())} entries)")
print("arsc stored:", z.getinfo("resources.arsc").compress_type == 0)
for k in PATCHED:
    print(f"  {k} == patched:", hashlib.sha256(z.read(k)).hexdigest() == hashlib.sha256(new[k]).hexdigest())
for k in KEEP_ORIG:
    print(f"  {k} == original:", z.read(k) == orig.read(k))
print("apk sha256:", hashlib.sha256(open(OUT, "rb").read()).hexdigest())
