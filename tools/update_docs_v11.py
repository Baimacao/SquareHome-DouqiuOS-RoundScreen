#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v11 发布：仅圆屏适配（去掉动态壁纸）+ 设置页只用应用验证过的控件。"""
import hashlib, io, os, re, subprocess, sys
W = r"E:\B1807\Documents\DSH\squarehome-mod"
sys.path.insert(0, os.path.join(W, "_tools"))
from publish_squarehome import api, cmd_publish, OWNER, REPO, BRANCH

APK = os.path.join(W, "SquareHome_3.0.1-douqiuos-v11-mod.apk")
sha = hashlib.sha256(open(APK, "rb").read()).hexdigest()
print("v11 sha256:", sha, "| size:", os.path.getsize(APK))

notes = """DouqiuOS 定制分支 · Square Home 3.0.1 — **mod 式 / 仅圆屏适配（v11）**

## 这一版做了什么

1. **去掉动态壁纸功能**（视频壁纸开关、路径设置、`DouqiuVideoWallpaper`、`fk.k` 跳过自绘壁纸的钩子，全部移除）。
2. **只保留圆屏适配本身**：应用抽屉列表的收边（贴弧 / 直栏）+ 上下边缘渐隐。
3. **修「打开应用抽屉设置就崩溃」**：上一版设置页里用了两个应用从未在该页用过的控件
   （`MyIntPreference` 配未知 key、`preferencex.EditTextPreference`），已全部去掉；
   现在这一组只有三个 **`MySwitchPreference`** —— 就是应用自己在同一页（「清單類型」那一行）用的控件。

## 改动面（整包只有 9 个条目与原包不同）

| 条目 | 内容 |
|---|---|
| `classes.dex` / `classes2.dex` | **仅 2 处钩子**（`AnimateGridView$a.onScroll`、`AnimateGridView.onLayout`）+ 新增 `com.ss.view.RoundScreenInsets` |
| `AndroidManifest.xml` | `versionName` = `3.0.1-douqiuos` |
| `res/xml/prefs_appdrawer.xml` | 三个开关 |
| `res/xml/prefs_about.xml` | About 页署名 |
| 4 个 OOBE 布局 | 底部按钮进圆内、页面 340→370px、安全区 58dp、「磚塊效果」可滚动 |

**`resources.arsc` 逐字节不动**，`classes4/5/6.dex`、assets、native so、其它资源也全部与原包逐字节相同；
旧签名与 `stamp-cert-sha256` 已去掉。`apksigner verify` v1/v2/v3 全 true。

## 设置（`設定 → 程式抽屜` →「DouqiuOS 適配」）

| 选项 | key | 默认 | 作用 |
|---|---|---|---|
| 圓屏適配 | `douqiuRoundFit` | 關 | 关 = 原版观感 |
| 直欄模式 | `douqiuRoundFitColumn` | 關 | 开 = 所有行同一栏；关 = 逐行贴弧（依赖「圓屏適配」） |
| 邊緣漸隱 | `douqiuFade` | 開 | 上下边缘淡出，**长度固定 = 底部导航栏高度**（`@dimen/menu_bar_height`） |

贴弧强度、渐隐大小、动画流速、视频壁纸这些旋钮本版**不提供**（它们需要 `MyIntPreference`/`EditTextPreference`，
正是崩溃嫌疑；等你确认设置页不再崩，我再逐个加回来）。
"""
io.open(os.path.join(W, "docs", "release-notes-v11.md"), "w", encoding="utf-8", newline="\n").write(notes)
print("notes -> docs/release-notes-v11.md")

readme = os.path.join(W, "docs", "README.md")
t = io.open(readme, encoding="utf-8").read()
t = re.sub(r"SquareHome_3\.0\.1-douqiuos-v10-mod\.apk", "SquareHome_3.0.1-douqiuos-v11-mod.apk", t)
t = re.sub(r"[0-9a-f]{64}", sha, t, count=1)
t = re.sub(r"## mod 式（v10，推荐）.*?## 产物", """## mod 式 / 仅圆屏适配（v11，推荐）

以**原包**为基底，只替换 2 个 dex + manifest + 6 个资源文件（共 9 个条目），`resources.arsc` 逐字节不动。
只做应用抽屉列表的圆屏收边（贴弧/直栏）与上下边缘渐隐；设置页只用应用验证过的 `MySwitchPreference`。
不含汉化补全（那需要重编译资源表）。

## 产物""", t, flags=re.S)
io.open(readme, "w", encoding="utf-8", newline="\n").write(t)

stage = os.path.join(W, "_tools", "stage_repo.py")
s = io.open(stage, encoding="utf-8").read()
s = s.replace("SquareHome_3.0.1-douqiuos-v10-mod.apk", "SquareHome_3.0.1-douqiuos-v11-mod.apk")
for extra in (r'"_tools\\assemble_v11.py", "tools/assemble_v11.py"',
              r'"_tools\\apply_v11_minimal.py", "tools/apply_v11_minimal.py"',
              r'"_tools\\update_docs_v11.py", "tools/update_docs_v11.py"',
              r'"build5.ps1", "tools/build5.ps1"'):
    if extra.split('"')[1] not in s:
        s = s.replace("]\n\nif os.path.exists(STAGE)", "    (" + extra + "),\n]\n\nif os.path.exists(STAGE)", 1)
io.open(stage, "w", encoding="utf-8", newline="\n").write(s)
subprocess.run([sys.executable, stage], check=True)

old = "apk/SquareHome_3.0.1-douqiuos-v10-mod.apk"
st, res = api("GET", f"/repos/{OWNER}/{REPO}/contents/{old}")
if st == 200:
    st2, _ = api("DELETE", f"/repos/{OWNER}/{REPO}/contents/{old}",
                 {"message": "chore: keep only latest apk in tree", "sha": res["sha"]})
    print("delete", old, "->", st2)

cmd_publish(os.path.join(W, "gh-staging"), "v11",
            "Square Home 3.0.1 · DouqiuOS 定制分支（v11：仅圆屏适配 / mod 式 / 修设置崩溃）",
            os.path.join(W, "docs", "release-notes-v11.md"), asset=APK)

st, tree = api("GET", f"/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1")
remote = {x["path"]: x["sha"] for x in tree["tree"] if x["type"] == "blob"}


def gbs(p):
    d = open(p, "rb").read()
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(d))
    h.update(d)
    return h.hexdigest()


base = os.path.join(W, "gh-staging")
ok = bad = 0
for root, _d, files in os.walk(base):
    for fn in files:
        full = os.path.join(root, fn)
        rel = os.path.relpath(full, base).replace("\\", "/")
        if rel not in remote or gbs(full) != remote[rel]:
            print("PROBLEM:", rel)
            bad += 1
        else:
            ok += 1
print(f"blob verify: {ok} ok, {bad} bad | tree files: {len(remote)}")
print("tree apks:", sorted(p for p in remote if p.startswith("apk/")))
st, rel = api("GET", f"/repos/{OWNER}/{REPO}/releases")
for r in rel[:2]:
    for a in r.get("assets", []):
        local = os.path.join(W, a["name"])
        if os.path.exists(local):
            ls = hashlib.sha256(open(local, "rb").read()).hexdigest()
            print(f"release {r['tag_name']} / {a['name']}: digest match =", a.get("digest") == "sha256:" + ls)
