#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# v12 publish: settings back (numeric + soft curve + animation speed), still mod-style.
import hashlib, io, os, re, subprocess, sys
W = r"E:\B1807\Documents\DSH\squarehome-mod"
sys.path.insert(0, os.path.join(W, "_tools"))
from publish_squarehome import api, cmd_publish, OWNER, REPO, BRANCH

APK = os.path.join(W, "SquareHome_3.0.1-douqiuos-v12-mod.apk")
sha = hashlib.sha256(open(APK, "rb").read()).hexdigest()
print("v12 sha256:", sha, "| size:", os.path.getsize(APK))

notes = """DouqiuOS 定制分支 · Square Home 3.0.1 — **圆屏适配（v12，mod 式）**

## 设置项都回来了（`設定 → 程式抽屜` →「DouqiuOS 適配」）

| 选项 | key | 默认 | 说明 |
|---|---|---|---|
| 圓屏適配 | `douqiuRoundFit` | 關 | 总开关；关 = 原版观感 |
| 直欄模式 | `douqiuRoundFitColumn` | 關 | 所有行同一栏（优先于柔性曲線） |
| **柔性曲線** | `douqiuSoftCurve` | 關 | 弧只跟到一定程度就停（上限 ≈33dp），行不会大幅参差 |
| 貼弧強度 | `douqiuFitStrength` | 100% | 50~200%；100% = 按圆弧精确计算 |
| 邊緣漸隱 | `douqiuFade` | 開 | 上下边缘淡出 |
| 漸隱大小 | `douqiuFadeScale` | 100% | 相对底部导航栏高度（100% = 与底栏同高） |
| **動畫流速** | `douqiuAnimSpeed` | 100% | 50~200%；抽屉项目动画 + 弹性回弹动画的时长倍率 |

四种观感：**關閉 / 貼弧（逐行跟随圆弧）/ 柔性曲線（跟随但有上限）/ 直欄（全部同一栏）**。

数值项用的是应用自己在同一页已经在用的 `MyIntPreference`（原版「文字大小」就是它），
对话框范围 50~200、步进 5、后缀 `%`。动态壁纸相关（开关、路径、`EditTextPreference`）已全部移除。

## 改动面：整包只有 9 个条目与原包不同

`classes.dex` + `classes2.dex`（**4 处钩子**：`AnimateGridView$a.onScroll` 里 2 处、
`AnimateGridView.onLayout` / `t()` 各 1 处）+ `AndroidManifest.xml`（versionName=`3.0.1-douqiuos`）
+ `res/xml/prefs_appdrawer.xml`、`res/xml/prefs_about.xml` + 4 个 OOBE 布局。

**`resources.arsc` 逐字节不动**，`classes3~6.dex`、assets、so、其它资源全部与原包逐字节相同；
签名 v1/v2/v3 全 true。
"""
io.open(os.path.join(W, "docs", "release-notes-v12.md"), "w", encoding="utf-8", newline="\n").write(notes)
print("notes -> docs/release-notes-v12.md")

readme = os.path.join(W, "docs", "README.md")
t = io.open(readme, encoding="utf-8").read()
t = re.sub(r"SquareHome_3\.0\.1-douqiuos-v11-mod\.apk", "SquareHome_3.0.1-douqiuos-v12-mod.apk", t)
t = re.sub(r"[0-9a-f]{64}", sha, t, count=1)
io.open(readme, "w", encoding="utf-8", newline="\n").write(t)

stage = os.path.join(W, "_tools", "stage_repo.py")
s = io.open(stage, encoding="utf-8").read()
s = s.replace("SquareHome_3.0.1-douqiuos-v11-mod.apk", "SquareHome_3.0.1-douqiuos-v12-mod.apk")
for extra in (r'"_tools\\assemble_v12.py", "tools/assemble_v12.py"',
              r'"_tools\\apply_v12_prefs.py", "tools/apply_v12_prefs.py"',
              r'"_tools\\update_docs_v12.py", "tools/update_docs_v12.py"',
              r'"build6.ps1", "tools/build6.ps1"'):
    if extra.split('"')[1] not in s:
        s = s.replace("]\n\nif os.path.exists(STAGE)", "    (" + extra + "),\n]\n\nif os.path.exists(STAGE)", 1)
io.open(stage, "w", encoding="utf-8", newline="\n").write(s)
subprocess.run([sys.executable, stage], check=True)

old = "apk/SquareHome_3.0.1-douqiuos-v11-mod.apk"
st, res = api("GET", f"/repos/{OWNER}/{REPO}/contents/{old}")
if st == 200:
    st2, _ = api("DELETE", f"/repos/{OWNER}/{REPO}/contents/{old}",
                 {"message": "chore: keep only latest apk in tree", "sha": res["sha"]})
    print("delete", old, "->", st2)

cmd_publish(os.path.join(W, "gh-staging"), "v12",
            "Square Home 3.0.1 · DouqiuOS 定制分支（v12：圆屏适配设置项 + 柔性曲線 + 动画流速）",
            os.path.join(W, "docs", "release-notes-v12.md"), asset=APK)

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
