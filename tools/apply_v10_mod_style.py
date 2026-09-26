#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v10（mod 式）：只改必要的资源文件，不新增任何资源、不重编译资源表。
   decoded/ 树里放“mod 式”版的 prefs_appdrawer.xml（标签全用字面量中文，模式用两个开关），
   apktool.yml 里改版本名。"""
import io, os, re, sys, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
DEC = os.path.join(W, "decoded")

ROWS = '''    <PreferenceCategory android:layout="@layout/l_kit_layout_pref_category" android:title="DouqiuOS 適配">
        <com.ss.squarehome2.preference.MySwitchPreference android:title="圓屏適配" android:summary="列表依圓弧收邊，避免被圓屏切掉（預設關閉）" android:key="douqiuRoundFit" android:defaultValue="false" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="直欄模式" android:summary="所有行對齊同一欄，不再逐行貼弧" android:key="douqiuRoundFitColumn" android:defaultValue="false" android:dependency="douqiuRoundFit" />
        <com.ss.squarehome2.preference.MyIntPreference android:title="貼弧強度" android:summary="收邊幅度，100% = 依圓弧精確計算" android:key="douqiuFitStrength" android:defaultValue="100" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="邊緣漸隱" android:summary="項目滾出上／下邊緣時淡出" android:key="douqiuFade" android:defaultValue="true" />
        <com.ss.squarehome2.preference.MyIntPreference android:title="漸隱大小" android:summary="相對底部導覽列高度，100% = 與導覽列同高" android:key="douqiuFadeScale" android:defaultValue="100" android:dependency="douqiuFade" />
        <com.ss.squarehome2.preference.MyIntPreference android:title="動畫流速" android:summary="抽屜項目動畫時長倍率，100% = 原速" android:key="douqiuAnimSpeed" android:defaultValue="100" />
        <com.ss.squarehome2.preference.MySwitchPreference android:title="視頻壁紙" android:summary="應用內硬解循環播放本地視頻當壁紙（MediaCodec）" android:key="douqiuVideoWallpaper" android:defaultValue="false" />
        <com.ss.preferencex.EditTextPreference android:title="視頻檔案路徑" android:summary="例：/sdcard/SquareHome2/wallpaper.mp4，留空則自動尋找" android:key="douqiuVideoPath" android:defaultValue="" android:dependency="douqiuVideoWallpaper" />
    </PreferenceCategory>'''

# 1) prefs_appdrawer.xml -> mod 式（清單類型之后插入，去掉 v9 那套 @string/@array 行）
p = os.path.join(DEC, "res", "xml", "prefs_appdrawer.xml")
t = io.open(p, encoding="utf-8").read()
t = re.sub(r'[ \t]*<PreferenceCategory[^>]*douqiu_pref_cat.*?</PreferenceCategory>\n', "", t, flags=re.S)
anchor = '<com.ss.squarehome2.preference.MySwitchPreference android:title="@string/list_type" android:key="appdrawerListType" />'
if anchor not in t:
    raise SystemExit("list_type row not found")
t = t.replace(anchor, anchor + "\n" + ROWS, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("prefs_appdrawer.xml rows:", t.count("douqiu"))

# 2) About 页署名：mod 式用字面量（沿用 decoded 里已有的版本，这里确保它是字面量版）
pa = os.path.join(DEC, "res", "xml", "prefs_about.xml")
t = io.open(pa, encoding="utf-8").read()
if "For：DouqiuOS" not in t:
    add = ('    <PreferenceCategory android:layout="@layout/l_kit_layout_pref_category" android:title="DouqiuOS 適配版">\n'
           '        <Preference android:selectable="false" android:title="For：DouqiuOS 适配　By：Baimacao" android:summary="非官方修改版 · 圓屏適配 + 應用程式清單視圖調整（3.0.1-douqiuos）" />\n'
           '    </PreferenceCategory>\n')
    t = t.replace('<androidx.preference.PreferenceScreen\n  xmlns:android="http://schemas.android.com/apk/res/android">\n',
                  '<androidx.preference.PreferenceScreen\n  xmlns:android="http://schemas.android.com/apk/res/android">\n' + add)
    io.open(pa, "w", encoding="utf-8", newline="\n").write(t)
print("prefs_about attribution:", "For：DouqiuOS" in io.open(pa, encoding="utf-8").read())

# 3) OOBE 的 4 个布局：沿用 v4 的版本（从 decoded 树里拷到 decoded10？不，两者都在 decoded）
print("OOBE layouts already edited in decoded/:",
      all(os.path.exists(os.path.join(DEC, "res", "layout", f)) for f in
          ("activity_wizard.xml", "layout_wizard_content_bg.xml", "wizard_advice.xml", "wizard_tile_effect.xml")))

# 4) apktool.yml 版本名
y = os.path.join(DEC, "apktool.yml")
t = io.open(y, encoding="utf-8").read()
t = re.sub(r"versionName: .*", "versionName: 3.0.1-douqiuos", t)
io.open(y, "w", encoding="utf-8", newline="\n").write(t)
print("apktool.yml:", re.search(r"versionName: .*", t).group(0))

# 5) $ 前缀资源改名（只为让 apktool 能完整编译资源，出货时不会用到这些文件）
DRAW = os.path.join(DEC, "res", "drawable")
n = 0
for fn in os.listdir(DRAW):
    if fn.startswith("$"):
        os.replace(os.path.join(DRAW, fn), os.path.join(DRAW, fn[1:]))
        n += 1
print("renamed $ drawables in decoded/:", n)
