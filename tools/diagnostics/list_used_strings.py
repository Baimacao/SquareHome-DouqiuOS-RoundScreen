#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 app 实际引用到的 string 资源列出来（mc.smali 字段 -> public.xml 名称 -> 各语言文案）。"""
import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DEC = r"E:\B1807\Documents\DSH\squarehome-mod\decoded"

ids = {}
for line in open(os.path.join(DEC, "res", "values", "public.xml"), encoding="utf-8"):
    m = re.search(r'<public type="(\w+)" name="([^"]+)" id="(0x[0-9a-f]+)"', line)
    if m:
        ids[m.group(3).lower()] = (m.group(1), m.group(2))

mc = os.path.join(DEC, "smali_classes4", "com", "ss", "squarehome2", "mc.smali")
fields = {}
for line in open(mc, encoding="utf-8"):
    m = re.match(r"\.field public static ([A-Za-z0-9_$]+):I = (0x[0-9a-f]+)", line.strip())
    if m:
        fields[m.group(1)] = m.group(2).lower()

# 取默认与 zh-rTW 文案
def load_values(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        m = re.match(r'\s*<string name="([^"]+)"[^>]*>(.*)</string>', line)
        if m:
            out[m.group(1)] = m.group(2)[:70]
    return out

en = load_values(os.path.join(DEC, "res", "values", "strings.xml"))
tw = load_values(os.path.join(DEC, "res", "values-zh-rTW", "strings.xml"))

KEY = re.compile(r"(about|version|praise|dev|thank|credit|licen|update|author|email|contact_us|more_app|websit|home_page|help|faq|price|purchase|backup|setting)", re.I)
print("app 引用到的 string 资源里，与 about/版本/开发者 相关的：")
for fname, rid in sorted(fields.items(), key=lambda kv: kv[1]):
    typ, name = ids.get(rid, ("?", "?"))
    if typ != "string":
        continue
    if KEY.search(name):
        print(f"  mc->{fname:<4} {rid}  {name:<28} en={en.get(name,'')!r}  tw={tw.get(name,'')!r}")
print("\napp 引用的 string 总数:", len(fields))
