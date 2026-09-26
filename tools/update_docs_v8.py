#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 发布：文档 + staging + 发布 + 核对。
v8 = 可调设置（模式/曲率/渐隐/动画/动态壁纸）+ 汉化补全 + 版本号 douqiuos 分支。"""
import hashlib, io, os, re, subprocess, sys
W = r"E:\B1807\Documents\DSH\squarehome-mod"
sys.path.insert(0, os.path.join(W, "_tools"))
from publish_squarehome import api, cmd_publish, OWNER, REPO, BRANCH

APK = os.path.join(W, "SquareHome_3.0.1-douqiuos-v8.apk")
sha = hashlib.sha256(open(APK, "rb").read()).hexdigest()
print("v8 sha256:", sha, "| size:", os.path.getsize(APK))

# ---------- 1) README：v8 段 ----------
readme = os.path.join(W, "docs", "README.md")
t = io.open(readme, encoding="utf-8").read()
t = re.sub(r"SquareHome_3\.0\.1_round-v7\.apk", "SquareHome_3.0.1-douqiuos-v8.apk", t)
t = re.sub(r"SquareHome_3\.0\.1_round-v6\.apk", "SquareHome_3.0.1-douqiuos-v8.apk", t)
t = re.sub(r"[0-9a-f]{64}", sha, t, count=1)

v8 = """
### 4. DouqiuOS 可调设置（v8 新增，`設定 → 程式抽屜`）

`prefs_appdrawer.xml` 里新增「DouqiuOS 適配」分组，全部写进应用默认 SharedPreferences：

| 选项 | key | 默认 | 说明 |
|---|---|---|---|
| 圓屏適配（模式） | `douqiuFitMode` | 0 = 關閉 | 0 關閉 / 1 貼弧 / 2 直欄 |
| 貼弧強度 | `douqiuFitStrength` | 100 % | 收邊幅度倍率（50~200%，`MyIntPreference` 提供对话框） |
| 邊緣漸隱 | `douqiuFade` | 開 | 項目滾出上/下邊緣時淡出 |
| 漸隱大小 | `douqiuFadeScale` | 100 % | **相對底部導覽列高度**（`@dimen/menu_bar_height`），100% = 与底栏一致 |
| 動畫流速 | `douqiuAnimSpeed` | 100 % | 抽屜項目動畫 / 彈性回彈動畫的時長倍率 |
| 動態桌布支援 | `douqiuLiveWallpaper` | 關 | 開：改由系統繪製壁紙（含動態壁紙），本應用不再自繪；關：原行為 |

实现：`RoundScreenInsets` 每帧读这些偏好；動畫流速挂在 `AnimateGridView.t()` /
`AnimateGridView$a.onScroll()` 的 `startAnimation` 前；動態壁紙则挂 `fk.k(Canvas)`（跳过自绘）
并给窗口加 `FLAG_SHOW_WALLPAPER` + 透明背景。

### 5. 汉化补全（v8）

原版 zh-rTW 缺 **66 条**、zh-rCN 缺 20 条 app 自己的文案（会回退成英文），v8 全部补齐
（品牌名 `app_name`、URL、`@string` 引用按惯例不动）。判据：`mc`（R.string 类）里 app 实际引用、
但 `values-zh-rTW` 没有值的条目。

### 6. 版本号：DouqiuOS 定制分支（v8）

`AndroidManifest.xml` 的 `versionName` → **`3.0.1-douqiuos`**（`versionCode` 保持 `30001`，
这样可以直接覆盖安装，不必卸载）。manifest 结构经 `aapt2 dump xmltree` 对比，与原包**只差这一处**。

> ⚠️ 注意：v8 为了让「汉化 + 新设置项」进入资源表，改为**整包资源重编译**（apktool + aapt2）。
> 资源表经逐条对比（忽略 apktool 的 `PUBLIC` 标记与 aapt2 合并的冗余 `-v4/-v21` 限定符）：
> 差异只有「我新增的字符串/数组」与「40 个 `$` 前缀的库内 AVD 资源改名」（ID 不变，
> 见下）。manifest 只差 versionName。dex 侧仍只动 3 个文件。
"""
if "可调设置（v8 新增" not in t:
    t = t.replace("## 产物", v8 + "\n## 产物", 1)
io.open(readme, "w", encoding="utf-8", newline="\n").write(t)
print("README updated:", "v8 新增" in t)

# ---------- 2) release notes ----------
notes = """DouqiuOS 定制分支 · Square Home 3.0.1（480×480 圆屏手表）

**装上后观感 = 原版**：所有改造都要自己在 `設定 → 程式抽屜 →「DouqiuOS 適配」`里打开。

## 本版（v8）新增

### 1) 设置里可直接调

| 选项 | 默认 | 范围/说明 |
|---|---|---|
| 圓屏適配 | 關閉 | 關閉 / 貼弧（緊貼圓邊）/ 直欄（同一欄對齊） |
| 貼弧強度 | 100% | 50~200%，收邊幅度（100% = 按圆弧精确计算） |
| 邊緣漸隱 | 開 | 項目滾出上/下邊緣時淡出 |
| 漸隱大小 | 100% | 50~200%，**相對底部導覽列高度**（100% = 跟底栏一样高） |
| 動畫流速 | 100% | 50~200%，抽屜項目 + 彈性回彈動畫的時長倍率 |
| 動態桌布支援 | 關 | 開：改由系統畫壁紙（**含動態壁紙**），本應用不再自繪 |

### 2) 汉化补全

原版 zh-rTW 缺 66 条、zh-rCN 缺 20 条应用文案（原本显示英文），全部补上
（例：「Live tile / 動態磚」「Monospace / 等寬字型」「Troubleshooting / 疑難排解」
「Set wallpaper to / 將桌布設為」「Work apps / 公司應用程式」…）。

### 3) 版本号标注为 DouqiuOS 定制分支

`versionName` = **3.0.1-douqiuos**（`versionCode` 不变 = 30001，可直接覆盖安装）。
About 页顶部另有 `For：DouqiuOS 适配　By：Baimacao`。

### 4) 已含的旧内容

- 应用列表圆屏适配（贴弧/直栏两种形状，可选强度）
- 上下边缘渐隐（长度默认与底部导航栏一致）
- OOBE 精靈：底部按钮移进圆内（原本**点不到**）；页面高度 340→370px；安全区 58dp；
  「磚塊效果」页可滚动（4 个选项都能点到）

## 安装

1. 先用 Square Home 自带「備份中心」导出设置。
2. 本包与之前的 v4~v7 **同签名** ⇒ 可直接覆盖安装；从原版换过来必须先卸载。
3. 装完去 `設定 → 程式抽屜` 最上面那组「DouqiuOS 適配」按需打开。

## 改动范围（v8 起为整包资源重编译）

- dex：仍只有 **3 个 smali 文件**（5 处钩子 + 新增 `com.ss.view.RoundScreenInsets`），
  `classes3/5/6.dex` 用原包逐字节不动。
- 资源：整包经 apktool + aapt2 重编译；资源表逐条对比的差异只有：
  ① 我新增的 `douqiu_*` 字符串/数组与 66+20 条汉化；② 40 个 `$` 前缀库内 AVD 资源改名
  （`$avd_*` → `avd_*`，aapt2 不接受 `$` 开头的资源名；ID 不变，引用它们的 18 个 XML 已同步更新）；
  ③ apktool 的 `PUBLIC` 标记与 aapt2 合并的冗余 `-v4/-v21` 限定符。
- manifest：`aapt2 dump xmltree` 对比，与原包**只差 versionName 一处**（394 行其余全同）。
- 签名：v1/v2/v3 全部通过。
"""
io.open(os.path.join(W, "docs", "release-notes-v8.md"), "w", encoding="utf-8", newline="\n").write(notes)
print("notes -> docs/release-notes-v8.md")

# ---------- 3) staging 列表更新 ----------
stage = os.path.join(W, "_tools", "stage_repo.py")
s = io.open(stage, encoding="utf-8").read()
s = s.replace("SquareHome_3.0.1_round-v7.apk", "SquareHome_3.0.1-douqiuos-v8.apk")
extra = """
    (r"_tools\\apply_v8_resources.py", "tools/apply_v8_resources.py"),
    (r"_tools\\fix_v8_resources.py", "tools/fix_v8_resources.py"),
    (r"_tools\\verify_v8_res2.py", "tools/verify_v8_resources.py"),
    (r"_tools\\assemble_v8.py", "tools/assemble_v8.py"),
    (r"_tools\\final_check_v8.py", "tools/final_check_v8.py"),
    (r"_tools\\list_missing_i18n.py", "tools/list_missing_i18n.py"),
    (r"_tools\\update_docs_v8.py", "tools/update_docs_v8.py"),
    (r"build3.ps1", "tools/build3.ps1"),
]"""
if "apply_v8_resources.py" not in s:
    s = s.replace("]\n\nif os.path.exists(STAGE)", extra + "\n\nif os.path.exists(STAGE)", 1)
io.open(stage, "w", encoding="utf-8", newline="\n").write(s)
print("stage_repo.py updated:", "apply_v8_resources.py" in s)
subprocess.run([sys.executable, stage], check=True)

# ---------- 4) 发布 ----------
old = "apk/SquareHome_3.0.1_round-v7.apk"
st, res = api("GET", f"/repos/{OWNER}/{REPO}/contents/{old}")
if st == 200:
    st2, _ = api("DELETE", f"/repos/{OWNER}/{REPO}/contents/{old}",
                 {"message": "chore: keep only latest apk in tree", "sha": res["sha"]})
    print("delete", old, "->", st2)

cmd_publish(os.path.join(W, "gh-staging"), "v8",
            "Square Home 3.0.1 · DouqiuOS 定制分支（v8：可调设置 + 汉化 + 版本号）",
            os.path.join(W, "docs", "release-notes-v8.md"), asset=APK)

# ---------- 5) 核对 ----------
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
