# Square Home「DouqiuOS 圓屏適配版」说明（v4）

> 表：**480×480 圆屏**，R=240px，内接方形 339px（`douqiu-os/docs/round-ui-design.md`）。
> 圆屏的**触摸区也被裁成圆盘** —— 落在四角的控件不只是看不见，是**点不到**。

## 1. 产物

| 文件 | 说明 |
|---|---|
| `SquareHome_3.0.1_round-v4.apk` | **本次交付**，已签名（v1+v2+v3）<br>sha256 `b8de6e85440c34876e0bcac7a3f0cfde7122bdc647d6fd9bf829a7bd88b51207` |
| `SquareHome_3.0.1_round-v3.apk` | 上一版（含圆屏适配开关 + OOBE 初版） |
| `squarehome-orig.apk` | 原包，回滚用 |

---

## 2. 这一版修的两件事

### ① 左/右下角按钮点不到

**原因**：`activity_wizard.xml` 里 `btnLeft`/`btnRight` 直接钉在**父容器左下/右下角**（`constraintBottom_toBottomOf=parent` + left/right），实测它们落在
`y≈450, x=37..71 / 410..444` —— 而圆盘在 y=450 只允许 `x∈[124,356]`，在 y=479 只剩 `x∈[218,262]`。
圆屏的触摸区就是圆盘，**所以这两个键既看不见也点不到**（第一页/最后一页就走不下去了）。

**改法**（`res/layout/activity_wizard.xml`）：

| 控件 | 改动 | 结果 |
|---|---|---|
| `btnLeft` | `layout_marginStart=86dp` + `layout_marginBottom=36dp` | 落在 `x≈105..205, y≈377..436` |
| `btnRight` | `layout_marginEnd=86dp` + `layout_marginBottom=36dp` | 落在 `x≈275..375, y≈377..436` |
| `pager` | 底边从「按钮上方」改为「父容器底部」 | 页面可用高度 340 → **370px**（按钮改为浮在页面底部之上） |
| `textTitle` | `layout_marginEnd=110dp` | 标题整体左移，右上角 `GUIDE` 不再探出圆外 |

按密度 1.22 换算校验：按钮四角都在圆内（最下沿 y=436 处圆盘允许 `x∈[101,379]`，按钮分别在 `105..205` / `275..375`）✓ 而且**圆心位置也在圆内** ⇒ 点得动 ✓。

### ② 内容比例不对

两个原因：

1. **我上一版把安全区做大了**：`72dp` = 88px，而内接方形只需要 `(480−339)/2 = 70.5px = 58dp`。
   ⇒ 全部改成 **58dp**（`layout_wizard_content_bg.xml`、`wizard_advice.xml`），卡片和内容都拿回 18% 的空间。
2. **精靈页面是按手机设计的**：例如「磚塊效果」页的内容（预览 150dp + 圆形勾选 + 背景效果 + 4 个单选）自然高度约 **500px**，
   而手表上页面区只有 ~370px ⇒ 原来的 4 个选项只有第一个「停用」露得出来，其余被裁掉（你截图里正是这样）。

**改法**（`res/layout/wizard_tile_effect.xml`）：把该页内容放进 `ScrollView`（`fillViewport=true`、`paddingBottom=96dp` 让内容能滚到按钮上方），
内层 `ConstraintLayout` 改成固定 `500dp` 高度 + 勾选框 `layout_constraintVertical_bias=0.34`。
⇒ 页面保持手机版的原始比例与字号，4 个选项**全都能看到、都能点**，只是需要上下滑一下。

---

## 3. v3/v2 已含的内容（未变）

- **圆屏适配开关**：`設定 → 程式抽屜` 前两行 —— `圓屏適配`（默认开，关掉即恢复原版）、`圓屏適配：直欄模式`（默认关）。
- **列表几何**：窗口坐标统一（圆心 = display 中心 − rootView 屏幕位置）+ 偏移上限 R/2，`offsetLeftAndRight()` 平移（不触发重排、命中框同步），行宽不变，长名称 `ellipsize=end`。
- **About 署名**：`設定 → 關於` 顶部 `For：DouqiuOS 适配　By：Baimacao`。

---

## 4. 验证

1. **补丁面**：最终 APK 与原包 smali 全树 diff —— 只有 3 个文件（2 个钩子 + `RoundScreenInsets.smali`）。
2. **APK 条目**：只换了 2 个 dex + 6 个资源文件；`resources.arsc`（仍 STORED）、`AndroidManifest.xml`、
   `classes3~6.dex`、其它资源**逐字节相同**；旧包 `stamp-cert-sha256` 已去掉。
3. **签名/对齐**：`apksigner verify` v1/v2/v3 全 true；`zipalign` 通过。
4. **资源核对**：`aapt2 dump xmltree` 确认按钮的 `marginStart/marginEnd/marginBottom=86/86/36dp`、
   pager 底边改为父容器、标题 `marginEnd=110dp`、卡片/advice 内缩 58dp、`tile_effect` 已包 `ScrollView`。

---

## 5. 安装

1. 先备份（應用自帶「備份中心」）。
2. **卸载原版** → 装 `SquareHome_3.0.1_round-v4.apk`（签名 `sdk/onyxremote.jks`，口令 `onyxremote`）。
3. 精靈里现在：`上一頁` / `下一頁/完成` 在圆内可点；「磚塊效果」页上下可滑，4 个选项都在。
4. 回滚：卸载后装回原包。

---

## 6. 仍未处理

- 抽屉**底部按钮条**（`x≈20..460, y≈428..474`）：圆盘在 y=474 只剩半宽 53px，原地怎么缩都不完整，要改只能整体上移或收窄。
- `tip_welcome` 等首次提示气泡：居中卡片高约 400px，四角可能被圆边切一点点。
- 精靈其他页面（`wizard_tile_size_p/_t`、`wizard_welcome`）内容居中、本来就在圆内；但底部按钮现在浮在页面下方，
  装饰性的手机预览图下端会与按钮重叠一点点（不影响操作）。

## 7. 复现脚本

| 脚本 | 作用 |
|---|---|
| `src\com\ss\view\RoundScreenInsets.java` | 列表圆屏几何 + 开关 |
| `build3.ps1` | 编译 helper → baksmali 原 dex → 插钩子（锚点自检）→ 汇编 dex |
| `rebuild_apk3.py` | 外科式重建 APK（`RES_FILES` 里列出被有意修改的资源） |
| `verify_dex4.ps1` / `final_check5.py` | smali diff / 产物完整性核对 |
| `measure_wizard.py` / `measure_labels.py` … | 从截图反推实际位置（诊断用） |
