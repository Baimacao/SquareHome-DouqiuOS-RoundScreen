# Square Home · DouqiuOS 圆屏适配 Mod

> 给 **480×480 圆屏手表**（DouqiuOS / SL8541E 平台）上的 **Square Home 3.0.1** 启动器做的圆屏适配改造：
> 应用列表视图不再被圆形边框切掉、OOBE 精靈能正常操作、About 页标明是修改版。
>
> **APK 已签名可直接安装**：见 [Releases](../../releases) 或仓库里的 `apk/`。
> 安装前必须**先卸载原版**（签名不同），建议先用 Square Home 自带的「備份中心」导出设置。

[English summary](#english-summary) · [改动清单](#改了什么) · [构建/复现](#怎么构建) · [免责声明](#免责声明)

---

## 背景：为什么直行不行

- 屏幕是 **480×480 圆盘**，R = 240px，物理可见区 = framebuffer 的内切圆；内接正方形 339px。
- 圆屏的**触摸区也是圆盘**：落在四角的控件不只是看不见，是**点不到**。
- Square Home 是手机桌面：应用列表是通栏直行、精靈页内容按 ~640dp 高的手机屏设计，
  在 393dp×393dp 的圆屏上必然被切。

## 改了什么

### 1. 应用列表（`程式抽屜 → 清單類型`）圆屏适配

- 每一行按**圆盘弦长**横向平移，让**图标左边缘贴着圆弧**走：越靠屏幕垂直中就越贴边、
  越靠上下越往里收 —— 不再有"直的一段"，也不会被圆边切。
- 实现细节（都是实测踩出来的）：
  - **统一坐标系**：圆心 = `DisplayMetrics` 中心 − `rootView` 屏幕位置，换算进**窗口坐标**；
    行位置用 `getLocationInWindow() + child.getTop()`。混用屏幕/display 坐标会让偏移整体偏一截
    （实机截图反推过：偏了约一个行距）。
  - 用 `View.offsetLeftAndRight()` 平移：**不触发重新布局**（滚动顺），且**同时移动 mLeft/mRight**
    ⇒ `AbsListView` 的 `getHitRect()` 命中框跟着走，点击位置和看到的图标一致。
  - **行宽不变**（不用 padding）⇒ 应用名不会被挤消失，只可能被圆边遮住（这是设计意图）。
  - 偏移量硬上限 `R/2`，任何情况都不会把某一行推到屏幕中间。
  - 长应用名补 `ellipsize=end`（原本是硬切半个字）。
- **开关**（`設定 → 程式抽屜`，紧跟「清單類型」）：
  | 开关 | key | 默认 | 作用 |
  |---|---|---|---|
  | 圓屏適配 | `douqiuRoundFit` | **关（默认不开启）** | 打开才开始收边；关掉 = 原版行为 |
  | 圓屏適配：直欄模式 | `douqiuRoundFitColumn` | 关 | 打开 = 所有行对齐同一栏（不逐行贴弧） |

  > **默认关闭**是刻意的：不动用户看到的默认观感，需要的人自己去开。
  > 打开后有两种形状可选：默认「逐行贴弧」（每行按圆盘弦长跟随，滚动时像波浪），
  > 或打开「直欄模式」（所有行同一栏，滚动时不动）。
- 只影响列表模式：`getNumColumns()==1` **且** adapter 是 `com.ss.squarehome2.g0`；
  网格模式、联系人等共用 `AnimateGridView` 的界面不受影响。

### 1b. 列表上下边缘渐隐（"翻出时淡化"）

- 用的是 **Android 原生 fading edge**（`AbsListView` 自带能力），不是自己画的遮罩：
  app 自己在 `d0.P0()` 里把它关掉了（`setVerticalFadingEdgeEnabled(false)`，长度只给 5dp），
  这里重新打开，长度**直接读应用自己的 `@dimen/menu_bar_height`**（底部导航栏高度 44dp ≈ 54px），
  所以渐隐带与底部导航栏永远一致；读不到时兜底 44dp。
- **必须同时 `setCacheColorHint(0)`**：否则渐隐区会被画成实心色块而不是透出壁纸（老坑）。
- 判断方式是"看状态"而不是"打标记"：一旦应用再把它关掉，下一次滚动会自动补回来。
- **与圆屏适配开关无关**，默认就有；上下两端各有渐隐（原生 API 不支持只做一端）。

### 2. OOBE（首次设置精靈）圆屏适配

- **底部按钮**：`上一頁` / `下一頁` / `完成` 原本钉在屏幕四角（实测 `y≈450, x=37..71 / 410..444`），
  在圆盘外 ⇒ **点不到**、也看不见。改为 `marginStart/End=86dp` + `marginBottom=36dp`，
  实测落在 `x≈105..205 / 275..375, y≈377..436`，四角都在圆内。
- **页面可用高度**：`ViewPager` 底边从「按钮上方」改到父容器底部（340 → 370px），按钮改为浮在页面之上。
- **安全区**：页面卡片/内容内缩按内接方形取 **58dp（≈70.5px）**，四角不再被圆边切；标题加
  `marginEnd=110dp`，右上角 `GUIDE` 不再探出圆外。
- **「磚塊效果」页可滚动**：该页内容自然高度约 500px 而页面只有 ~370px，原本 4 个背景效果选项
  只露出第一个。现在包进 `ScrollView`（保持手机版原始比例与字号），4 个选项都能看到、都能点。

### 3. About 页署名

`設定 → 關於` 顶部新增一组：

```
DouqiuOS 適配版
For：DouqiuOS 适配　By：Baimacao
非官方修改版 · 圓屏適配 + 應用程式清單視圖調整（Square Home 3.0.1）
```


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

### 7. 应用内视频壁纸（v9）

`視頻壁紙` 开关 + `視頻檔案路徑`：用 `MediaPlayer`（MediaCodec 硬解）+ `SurfaceView`
在最底层循环播放本地视频当壁纸，跳过应用自绘壁纸；**不走系统 Live Wallpaper 服务**（手表没有），
也没有打包 FFmpeg（FFmpeg 在 Android 上的硬解同样转调 MediaCodec）。

## 产物

| 文件 | 说明 |
|---|---|
| `apk/SquareHome_3.0.1-douqiuos-v9.apk` | 已签名（v1+v2+v3），可直接安装<br>sha256 `245c796ace51fe4a8cd14efd2c62019a6e96a752d5ce835edf6bd52c347eeec5` |
| `patch/java/…/RoundScreenInsets.java` | 圆屏几何 + 开关（约 200 行） |
| `patch/res/…` | 改过的资源源文件（6 个：About/抽屉设置 XML + 4 个精靈布局） |
| `docs/patch-hooks.md` | smali 钩子落点与定位方法 |
| `docs/README-round-screen.md` | 详细的改动说明 + 截图反推诊断 + 验证记录 |
| `tools/` | 可复跑的构建与校验脚本（apktool/smali/d8/apksigner） |

改动范围（经 smali 全树 diff + APK 条目逐字节核对）：
**2 个 dex 的 3 个 smali 文件 + 6 个资源文件**；`resources.arsc`、`AndroidManifest.xml`、
`classes3~6.dex`、assets、native so、其它资源**逐字节未改**。

## 怎么构建

依赖：JDK 11+、Android build-tools（`aapt2/d8/zipalign/apksigner/dexdump`）、
[apktool](https://maven.apache.org/) 3.0.3（本项目从 Maven Central 取 `org.apktool:apktool-cli:3.0.3`，
内含 smali/baksmali）。

```powershell
# 1) 反编译原包
java -jar _tools\lib\apktool-cli-3.0.3.jar d -f -o decoded squarehome-orig.apk

# 2) 改资源（patch/res 下的 6 个文件覆盖进 decoded/res/...），然后
java -jar _tools\lib\apktool-cli-3.0.3.jar b decoded -o built-res.apk

# 3) 编译 helper 并给两个 dex 打钩子（带锚点自检）
powershell -File tools\build3.ps1

# 4) 外科式重建 APK：只换 2 个 dex + 6 个资源文件，其余条目压缩方式/属性照抄
python tools\rebuild_apk3.py

# 5) 对齐 + 签名 + 校验
zipalign -p -f 4 <in.apk> <aligned.apk>
apksigner sign --ks <your.jks> --out SquareHome_3.0.1_round.apk <aligned.apk>
python tools\final_check5.py     # 产物完整性
powershell -File tools\verify_dex4.ps1   # smali 全树 diff（证明补丁面）
```

⚠️ **应用升级后**：R8 后的短名会变（`g0`、`AnimateGridView$a`、`kc->K`、`frameIcon` 的 id 等）。
`build3.ps1` 会先做锚点自检，找不到会直接报错而不是产出坏包；
`RoundScreenInsets.java` 里的 `LIST_ADAPTER` / `ID_FRAME_ICON` / `ID_TEXT_LABEL` 需按新版重查
（方法见 `docs/patch-hooks.md`）。

## 验证记录

- smali 全树 diff：只有 3 个文件变化（2 个钩子 + 新增 helper 类）。
- `apksigner verify`：v1/v2/v3 全 true；`zipalign -c 4` 通过；`aapt2 dump badging` 包名/版本未变
  （`com.ss.squarehome2` 3.0.1 / 30001）。
- `resources.arsc` 仍为 STORED；`classes3~6.dex`、manifest、assets、so 与原包逐字节相同。
- 圆屏几何与按钮落点用截图逐像素反推校验（见 `tools/diagnostics/`）。

## 免责声明

- **Square Home 是第三方商业应用**（作者 ChYK），本仓库**不包含其源码**，只包含针对该版本的
  二进制补丁脚本、补丁源码、以及一个**已修改并重新签名**的 APK，供个人在自备设备上做圆屏适配使用。
  请自行确认在你的使用场景下合法；如果你要长期分发，建议只分发 **补丁脚本** 而不是 APK 本体。
- 重新签名会改变应用签名 ⇒ 必须卸载原版才能安装，且**应用数据会被清除**（请先备份）。
- 版权归原作者；本改造与原作者无关。

---

## English summary

A round-screen (480×480, R=240px) adaptation mod for **Square Home 3.0.1** on the DouqiuOS / SL8541E watch:

1. **App-drawer list** (the adaptation is **off by default**; enable it in *Settings → App drawer*): each row is
   sizes/row width unchanged, names are never squeezed away, hit rects move with the view.
   Two switches in *Settings → App drawer*: master on/off, plus a "straight column" mode.
2. **OOBE wizard**: the corner buttons (`prev`/`next`/`finish`) were outside the disc and therefore
   **untappable** — they are now inset inside the circle; page area grew 340→370px; safe-area insets are
   exactly the inscribed square (58dp); the overflowing "tile effect" page is scrollable so all 4 options
   are reachable.
3. **About page** now shows `For：DouqiuOS 适配　By：Baimacao`.

Only 3 smali files and 6 resource files differ; everything else in the APK is byte-identical.
Install requires uninstalling the original (different signature). Square Home itself is a third-party
commercial app — no source is included here.
