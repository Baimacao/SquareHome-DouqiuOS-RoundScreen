#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v11（mod 式 / 仅圆屏适配）：
   1) 去掉动态壁纸：删源文件、设置行只留三个开关（都用应用自己用过的 MySwitchPreference）
   2) 设置组里不再出现 MyIntPreference(未知 key) / EditTextPreference —— 这两个是“打开抽屉设置就崩”
      的最大嫌疑，去掉后设置页只用应用已验证过的控件。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
DEC = os.path.join(W, "decoded")

rows = '''    <PreferenceCategory android:layout="@layout/l_kit_layout_pref_category" android:title="DouqiuOS 適配">
        <com.ss.squarehome2.preference.MySwitchPreference android:title="圓屏適配" android:summary="列表依圓弧收邊，避免被圓屏切掉（預設關閉）" android:key="douqiuRoundFit" android:defaultValue="false" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="直欄模式" android:summary="所有行對齊同一欄，不再逐行貼弧" android:key="douqiuRoundFitColumn" android:defaultValue="false" android:dependency="douqiuRoundFit" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="邊緣漸隱" android:summary="項目滾出上／下邊緣時淡出（長度同底部導覽列）" android:key="douqiuFade" android:defaultValue="true" />
    </PreferenceCategory>'''

p = os.path.join(DEC, "res", "xml", "prefs_appdrawer.xml")
t = io.open(p, encoding="utf-8").read()
if "douqiuFitStrength" in t:
    anchor = '<com.ss.squarehome2.preference.MySwitchPreference android:title="@string/list_type" android:key="appdrawerListType" />'
    t = anchor + "\n" + rows + "\n"
    # 重建：保留原有除 douqiu 组以外的所有行
    body = io.open(p, encoding="utf-8").read()
    body = re.sub(r'[ \t]*<PreferenceCategory[^>]*DouqiuOS[^>]*>.*?</PreferenceCategory>\n', "", body, flags=re.S)
    body = body.replace(anchor, anchor + "\n" + rows, 1)
    t = body
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("prefs_appdrawer.xml ->", [l.strip()[:60] for l in io.open(p, encoding="utf-8") if "douqiu" in l])

# 2) 删掉动态壁纸源码（不再编译、不再有相关偏好）
vp = os.path.join(W, "src", "com", "ss", "view", "DouqiuVideoWallpaper.java")
if os.path.exists(vp):
    os.remove(vp)
    print("removed src/com/ss/view/DouqiuVideoWallpaper.java")
