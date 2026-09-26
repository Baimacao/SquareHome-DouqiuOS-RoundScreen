#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v10（mod 式）发布：文档 + staging + 发布 + 核对。"""
import hashlib, io, os, re, subprocess, sys
W = r"E:\B1807\Documents\DSH\squarehome-mod"
sys.path.insert(0, os.path.join(W, "_tools"))
from publish_squarehome import api, cmd_publish, OWNER, REPO, BRANCH

APK = os.path.join(W, "SquareHome_3.0.1-douqiuos-v10-mod.apk")
sha = hashlib.sha256(open(APK, "rb").read()).hexdigest()
print("v10 sha256:", sha, "| size:", os.path.getsize(APK))

notes = """DouqiuOS 定制分支 · Square Home 3.0.1（480×480 圆屏手表）— **mod 式（最小改动）版**

> 这一版改成「以原包为基底、只换必要的几个文件」，**资源表 `resources.arsc` 逐字节不动**，
> 所以改动面可以逐条核对：整包 1591 个条目里**只有 10 个**与原包不同。

## 改动面（就这 10 个）

| 条目 | 内容 |
|---|---|
| `classes.dex` / `classes2.dex` / `classes4.dex` | 5 处钩子 + 新增 `com.ss.view.RoundScreenInsets`、`com.ss.view.DouqiuVideoWallpaper` |
| `AndroidManifest.xml` | `versionName` = **3.0.1-douqiuos**（结构其余部分与原包一致） |
| `res/xml/prefs_appdrawer.xml` | 新增「DouqiuOS 適配」设置组（标签用字面量中文，**不新增资源**） |
| `res/xml/prefs_about.xml` | About 页顶部署名 |
| `res/layout/activity_wizard.xml` 等 4 个 | OOBE 精靈：底部按钮进圆内、页面 340→370px、安全区 58dp、「磚塊效果」可滚动 |

其余全部（`resources.arsc`、其他 dex、assets、native so、所有其它资源）与原包**逐字节相同**；
旧签名与 `stamp-cert-sha256` 已去掉。`apksigner verify` v1/v2/v3 全 true。

## 设置（`設定 → 程式抽屜` →「DouqiuOS 適配」）

| 选项 | key | 默认 | 说明 |
|---|---|---|---|
| 圓屏適配 | `douqiuRoundFit` | 關 | 开关；关 = 原版观感 |
| 直欄模式 | `douqiuRoundFitColumn` | 關 | 开 = 所有行对齐同一栏；关 = 逐行贴弧 |
| 貼弧強度 | `douqiuFitStrength` | 100% | 50~200% |
| 邊緣漸隱 | `douqiuFade` | 開 | 上下边缘渐隐 |
| 漸隱大小 | `douqiuFadeScale` | 100% | 相对底部导航栏高度（100% = 与底栏同高） |
| 動畫流速 | `douqiuAnimSpeed` | 100% | 50~200% |
| 視頻壁紙 | `douqiuVideoWallpaper` | 關 | 应用内 MediaCodec 硬解循环播放本地视频当壁纸 |
| 視頻檔案路徑 | `douqiuVideoPath` | 空 | 例 `/sdcard/SquareHome2/wallpaper.mp4`；空则自动找几个常见位置 |

## 与「完整版」的差别（重要）

mod 式**不新加任何资源** ⇒ **不含 v8 做的「汉化补全」**（那 66/20 条文案存在资源表里，
必须整包重编译资源才能加）。如果你要汉化，用 v9（同样是 `3.0.1-douqiuos`，且已修掉 v8 的崩溃）；
两版装法一样，但**汉化与 mod 式只能二选一**（mod 式不重编译资源表）。

## 崩溃修复（v8 → 这里）

v8 的钩子插入用了"整文件替换"，`fk.smali` 里 `sget-object v0, ...->b:Landroid/app/WallpaperManager;`
出现在 7 个方法中，其中 `static s()Landroid/app/WallpaperManager;` 必须返回值却被插入了 `return-void`
⇒ dex 校验失败 ⇒ 崩溃。本版按**方法级定位**插入，并逐个核对出货 dex 的落点：
`applyToGridView` → `AnimateGridView$a.onScroll` / `AnimateGridView.onLayout`；
`scaleAnimation` → `AnimateGridView.t()` / `onScroll`；`skipWallpaper` → **仅** `fk.k(Canvas)`。
"""
io.open(os.path.join(W, "docs", "release-notes-v10.md"), "w", encoding="utf-8", newline="\n").write(notes)
print("notes -> docs/release-notes-v10.md")

readme = os.path.join(W, "docs", "README.md")
t = io.open(readme, encoding="utf-8").read()
t = re.sub(r"SquareHome_3\.0\.1-douqiuos-v9\.apk", "SquareHome_3.0.1-douqiuos-v10-mod.apk", t)
t = re.sub(r"[0-9a-f]{64}", sha, t, count=1)
if "mod 式（最小改动）版" not in t:
    t = t.replace("## 产物", """## mod 式（v10，推荐）

以**原包**为基底，只替换 3 个 dex + manifest + 6 个资源文件（共 10 个条目），
`resources.arsc` 逐字节不动 ⇒ 改动面可逐条核对。代价：**不含汉化补全**（汉化必须重编译资源表，
用 v9）。设置项、OOBE 适配、视频壁纸、版本名都在。

## 产物""", 1)
io.open(readme, "w", encoding="utf-8", newline="\n").write(t)

stage = os.path.join(W, "_tools", "stage_repo.py")
s = io.open(stage, encoding="utf-8").read()
s = s.replace("SquareHome_3.0.1-douqiuos-v9.apk", "SquareHome_3.0.1-douqiuos-v10-mod.apk")
for extra in (r'"_tools\\assemble_v10.py", "tools/assemble_v10.py"',
              r'"_tools\\apply_v10_mod_style.py", "tools/apply_v10_mod_style.py"',
              r'"_tools\\update_docs_v10.py", "tools/update_docs_v10.py"',
              r'"src\\com\\ss\\view\\DouqiuVideoWallpaper.java", "patch/java/com/ss/view/DouqiuVideoWallpaper.java"'):
    key = extra.split('"')[1]
    if key not in s:
        s = s.replace("]\n\nif os.path.exists(STAGE)", "    (" + extra + "),\n]\n\nif os.path.exists(STAGE)", 1)
io.open(stage, "w", encoding="utf-8", newline="\n").write(s)
subprocess.run([sys.executable, stage], check=True)

old = "apk/SquareHome_3.0.1-douqiuos-v9.apk"
st, res = api("GET", f"/repos/{OWNER}/{REPO}/contents/{old}")
if st == 200:
    st2, _ = api("DELETE", f"/repos/{OWNER}/{REPO}/contents/{old}",
                 {"message": "chore: keep only latest apk in tree", "sha": res["sha"]})
    print("delete", old, "->", st2)

cmd_publish(os.path.join(W, "gh-staging"), "v10",
            "Square Home 3.0.1 · DouqiuOS 定制分支（v10：mod 式最小改动 + 视频壁纸 + 修复崩溃）",
            os.path.join(W, "docs", "release-notes-v10.md"), asset=APK)

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
