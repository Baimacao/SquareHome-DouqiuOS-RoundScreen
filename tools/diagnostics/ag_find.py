#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 androguard 精确定位：谁引用了 layout/item_appdrawer_list 以及抽屉列表相关方法。"""
import sys, io, re, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = r"E:\B1807\Documents\DSH\squarehome-mod\squarehome-orig.apk"
W = r"E:\B1807\Documents\DSH\squarehome-mod"
TARGETS = {0x7f0c0054: "layout/item_appdrawer_list",
           0x7f0c0055: "layout/item_appdrawer_list_tablet",
           0x7f0c007e: "layout/layout_appdrawer",
           0x7f0700dd: "dimen/listtype_icon_size",
           0x7f0700de: "dimen/listtype_icon_size_tablet",
           0x7f0700df: "dimen/listtype_text_size",
           0x7f0700e0: "dimen/listtype_text_size_tablet"}

z = zipfile.ZipFile(APK)
names = sorted([n for n in z.namelist() if re.match(r"classes\d*\.dex$", n)],
               key=lambda s: (len(s), s))

ss_classes = []
hits = []
for n in names:
    dex = DEX(z.read(n))
    for cls in dex.get_classes():
        cn = cls.get_name()
        if cn.startswith("Lcom/ss/"):
            ss_classes.append(cn)
        if not cn.startswith("Lcom/ss/"):
            continue
        for m in cls.get_methods():
            code = m.get_code()
            if code is None:
                continue
            try:
                insns = code.get_bc().get_instructions()
            except Exception:
                continue
            found = set()
            for ins in insns:
                nm = ins.get_name()
                if nm.startswith("const"):
                    try:
                        lits = ins.get_literals()
                    except Exception:
                        continue
                    for lit in lits:
                        if lit in TARGETS:
                            found.add(TARGETS[lit])
            if found:
                hits.append((n, cn, m.get_name(), m.get_descriptor(), sorted(found)))

print("### resource references ###")
for h in hits:
    print(f"{h[0]} {h[1]}->{h[2]}{h[3]}  {h[4]}")

with open(W + r"\com_ss_classes.txt", "w", encoding="utf-8") as f:
    for x in sorted(ss_classes):
        f.write(x + "\n")
print("\ncom/ss classes:", len(ss_classes), "-> com_ss_classes.txt")
