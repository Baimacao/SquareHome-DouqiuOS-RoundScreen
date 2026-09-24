# 补丁落点（smali 钩子）

本 mod 只改 **3 个 smali 文件**（其余 dex 一个字节没动）。定位方法：
`res/layout/item_appdrawer_list.xml` 的资源 ID（本版本为 `0x7f0c0054`）→ 找谁 `sget` 它
（`com.ss.squarehome2.kc;->K:I`）→ 得到应用抽屉列表适配器 `com.ss.squarehome2.g0`，
它继承 `com.ss.squarehome2.d0$n`（`ArrayAdapter`），由 `com.ss.squarehome2.d0`（抽屉 FrameLayout）在
`P0()` 里创建；列表容器是 `com.ss.view.AnimateGridView`（`GridView` 子类）。

## 钩子 1 —— 每次滚动后重算（`classes.dex`）

文件：`com/ss/view/AnimateGridView$a.smali`
方法：`onScroll(Landroid/widget/AbsListView;III)V`（该方法在每次滚动/布局后都会被调用）

```smali
.method public onScroll(Landroid/widget/AbsListView;III)V
    .registers 13

    # >>> DouqiuOS round-screen hook (added): re-inset list rows on every scroll
    iget-object v0, p0, Lcom/ss/view/AnimateGridView$a;->e:Lcom/ss/view/AnimateGridView;

    invoke-static {v0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V

    iget-object v0, p0, Lcom/ss/view/AnimateGridView$a;->e:Lcom/ss/view/AnimateGridView;
    ...（原有代码不变）
```

## 钩子 2 —— 布局完成后补一次（`classes2.dex`）

文件：`com/ss/view/AnimateGridView.smali`
方法：`onLayout(ZIIII)V`

```smali
.method protected onLayout(ZIIII)V
    .registers 6

    invoke-super/range {p0 .. p5}, Landroid/widget/GridView;->onLayout(ZIIII)V
    # >>> DouqiuOS round-screen hook (added): inset list rows after layout
    invoke-static {p0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V
```

## 新增类（`classes2.dex`）

`com/ss/view/RoundScreenInsets` —— 源码见 `patch/java/com/ss/view/RoundScreenInsets.java`，
用 `javac --release 11 -cp android.jar` → `d8 --min-api 21` → `baksmali` 得到 smali 后放进
`smali_classes2/com/ss/view/`。

## 为什么要这么挂钩

- `AnimateGridView` 是抽屉列表（1 列）**和**网格模式共用的容器，所以 helper 里有两道闸：
  `getNumColumns() == 1` **且** adapter 类名是 `com.ss.squarehome2.g0`（列表模式专用适配器）。
- 滚动时 `AbsListView` 只重排子视图、不会走 `onLayout`，所以必须挂在 `onScroll` 上；`onLayout`
  那一处是为了首帧和偏好设置改动后立刻生效。
- helper 整体包在 `try/catch (Throwable)` 里：任何异常都只是"不生效"，不会让桌面崩。
