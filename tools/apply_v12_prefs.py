#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v12：把圆屏适配的设置项加回来（数值型 + 柔性曲線 + 动画流速），仍然 mod 式、不加新资源。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
DEC = os.path.join(W, "decoded")

rows = '''    <PreferenceCategory android:layout="@layout/l_kit_layout_pref_category" android:title="DouqiuOS 適配">
        <com.ss.squarehome2.preference.MySwitchPreference android:title="圓屏適配" android:summary="列表依圓弧收邊，避免被圓屏切掉（預設關閉）" android:key="douqiuRoundFit" android:defaultValue="false" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="直欄模式" android:summary="所有行對齊同一欄（優先於柔性曲線）" android:key="douqiuRoundFitColumn" android:defaultValue="false" android:dependency="douqiuRoundFit" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="柔性曲線" android:summary="弧只跟到一定程度就停，行不會大幅參差" android:key="douqiuSoftCurve" android:defaultValue="false" android:dependency="douqiuRoundFit" />
        <com.ss.squarehome2.preference.MyIntPreference android:title="貼弧強度" android:summary="收邊幅度，100% = 依圓弧精確計算" android:key="douqiuFitStrength" android:defaultValue="100" android:dependency="douqiuRoundFit" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="邊緣漸隱" android:summary="項目滾出上／下邊緣時淡出" android:key="douqiuFade" android:defaultValue="true" />
        <com.ss.squarehome2.preference.MyIntPreference android:title="漸隱大小" android:summary="相對底部導覽列高度，100% = 與導覽列同高" android:key="douqiuFadeScale" android:defaultValue="100" android:dependency="douqiuFade" />
        <com.ss.squarehome2.preference.MyIntPreference android:title="動畫流速" android:summary="抽屜項目動畫時長倍率，100% = 原速" android:key="douqiuAnimSpeed" android:defaultValue="100" />
    </PreferenceCategory>'''

p = os.path.join(DEC, "res", "xml", "prefs_appdrawer.xml")
t = io.open(p, encoding="utf-8").read()
anchor = '<com.ss.squarehome2.preference.MySwitchPreference android:title="@string/list_type" android:key="appdrawerListType" />'
if anchor not in t:
    raise SystemExit("list_type row not found")
t = re.sub(r'[ \t]*<PreferenceCategory[^>]*DouqiuOS[^>]*>.*?</PreferenceCategory>\n', "", t, flags=re.S)
t = t.replace(anchor, anchor + "\n" + rows, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("rows now:")
for l in io.open(p, encoding="utf-8"):
    if "douqiu" in l:
        print("   ", l.strip()[:112])
