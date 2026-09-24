#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯手工解析 dex，找出引用指定常量（资源 ID）的类/方法。

不依赖 androguard 的常量提取，直接按 dex 结构定位 code_item，
再把字节偏移映射回 class_data 的 method（code_off 精确匹配）。
"""
import sys, io, zipfile, re, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APK = r"E:\B1807\Documents\DSH\squarehome-mod\squarehome-orig.apk"
TARGETS = {
    0x7f0c0054: "layout/item_appdrawer_list",
    0x7f0c0055: "layout/item_appdrawer_list_tablet",
    0x7f0c007e: "layout/layout_appdrawer",
    0x7f0700dd: "dimen/listtype_icon_size",
    0x7f0700df: "dimen/listtype_text_size",
    0x7f0700de: "dimen/listtype_icon_size_tablet",
    0x7f0700e0: "dimen/listtype_text_size_tablet",
}


def uleb(d, off):
    r = 0; s = 0
    while True:
        b = d[off]; off += 1
        r |= (b & 0x7F) << s
        if not b & 0x80:
            return r, off
        s += 7


class Dex:
    def __init__(self, data):
        self.d = data
        (self.string_ids_size, self.string_ids_off, self.type_ids_size, self.type_ids_off,
         self.proto_ids_size, self.proto_ids_off, self.field_ids_size, self.field_ids_off,
         self.method_ids_size, self.method_ids_off, self.class_defs_size,
         self.class_defs_off) = struct.unpack_from("<IIIIIIIIIIII", data, 0x38)
        self.map_off = struct.unpack_from("<I", data, 0x34)[0]

    def str(self, i):
        off = struct.unpack_from("<I", self.d, self.string_ids_off + i * 4)[0]
        _, p = uleb(self.d, off)
        e = self.d.index(b"\x00", p)
        return self.d[p:e].decode("utf-8", "replace")

    def type_desc(self, i):
        return self.str(struct.unpack_from("<I", self.d, self.type_ids_off + i * 4)[0])

    def method_info(self, i):
        cls, proto, name = struct.unpack_from("<HHI", self.d, self.method_ids_off + i * 8)
        return self.type_desc(cls), self.str(name)

    def code_items(self):
        """yield (code_off, insns_off, insns_size)"""
        p = self.map_off
        n = struct.unpack_from("<I", self.d, p)[0]
        for k in range(n):
            off = p + 4 + k * 12
            typ, _unused, size, data_off = struct.unpack_from("<HHII", self.d, off)
            if typ == 0x2001:
                for j in range(size):
                    co = struct.unpack_from("<I", self.d, data_off + j * 4)[0]
                    if co == 0:
                        continue
                    insns_size = struct.unpack_from("<I", self.d, co + 12)[0]
                    yield co, co + 16, insns_size

    def methods_with_code(self):
        """yield (code_off, class_desc, method_name, method_idx)"""
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i * 32
            class_idx = struct.unpack_from("<I", self.d, off)[0]
            cdesc = self.type_desc(class_idx)
            cd_off = struct.unpack_from("<I", self.d, off + 24)[0]
            if not cd_off:
                continue
            p = cd_off
            sf, p = uleb(self.d, p); inf, p = uleb(self.d, p)
            dm, p = uleb(self.d, p); vm, p = uleb(self.d, p)
            for _ in range(sf + inf):
                _, p = uleb(self.d, p); _, p = uleb(self.d, p)
            for cnt in (dm, vm):
                midx = 0
                for _ in range(cnt):
                    diff, p = uleb(self.d, p)
                    _flags, p = uleb(self.d, p)
                    code, p = uleb(self.d, p)
                    midx += diff
                    if code:
                        _c, mname = self.method_info(midx)
                        yield code, cdesc, mname, midx


z = zipfile.ZipFile(APK)
dexnames = sorted([n for n in z.namelist() if re.match(r"classes\d*\.dex$", n)],
                  key=lambda s: (len(s), s))

for n in dexnames:
    data = z.read(n)
    dx = Dex(data)
    # 每个 dex 里逐个目标：先找字节位置
    for rid, label in TARGETS.items():
        pat = struct.pack("<I", rid)
        start = 0
        positions = []
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            positions.append(i)
            start = i + 1
        if not positions:
            continue
        methods = list(dx.methods_with_code())
        for pos in positions:
            hit = None
            for code_off, cdesc, mname, midx in methods:
                insns_off = code_off + 16
                size = struct.unpack_from("<I", data, code_off + 12)[0]
                if insns_off <= pos < insns_off + size * 2:
                    hit = (cdesc, mname, code_off, size)
                    break
            if hit:
                print(f"{n} {label} 0x{rid:08x} @0x{pos:x} -> {hit[0]}::{hit[1]} (code_off=0x{hit[2]:x}, insns={hit[3]})")
            else:
                print(f"{n} {label} 0x{rid:08x} @0x{pos:x} -> (not inside any code_item; static value / encoded array)")
