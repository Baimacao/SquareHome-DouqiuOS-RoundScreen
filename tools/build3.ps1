#!/usr/bin/env pwsh
# Build patched dexes (v8): helper + 5 hook insertions across classes.dex / classes2.dex / classes4.dex
# NOTE: keep this file ASCII-only (PowerShell 5.1 reads .ps1 as ANSI when there is no BOM).
$ErrorActionPreference = 'Stop'
$w = 'E:\B1807\Documents\DSH\squarehome-mod'
$jar = "$w\_tools\lib\apktool-cli-3.0.3.jar"
$aj = 'E:\B1807\Documents\DSH\sdk\platform\android.jar'
$d8 = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\d8.bat'
$dd = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\dexdump.exe'
$work = "$w\work3"
New-Item -ItemType Directory -Force -Path "$work\base","$work\classes","$work\helper","$work\patched" | Out-Null

function Insert-Before($path, $anchor, $insert, $tag) {
    $t = Get-Content $path -Raw -Encoding utf8
    if ($t -notmatch [regex]::Escape($anchor)) { throw "anchor [$tag] not found in $path" }
    $t = $t.Replace($anchor, ($insert.TrimEnd("`r", "`n") + "`n`n" + $anchor))
    [System.IO.File]::WriteAllText($path, $t, (New-Object System.Text.UTF8Encoding($false)))
    "  hook [$tag] ok"
}

# ---------- 1) helper ----------
"=== [1] javac RoundScreenInsets ==="
Remove-Item -Recurse -Force "$work\classes" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\classes" | Out-Null
javac --release 11 -nowarn -cp $aj -d "$work\classes" "$w\src\com\ss\view\RoundScreenInsets.java" 2>&1
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }

"=== [2] d8 + baksmali helper ==="
Remove-Item -Recurse -Force "$work\dexout","$work\helper" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\dexout" | Out-Null
& $d8 --min-api 21 --output "$work\dexout" "$work\classes\com\ss\view\RoundScreenInsets.class" 2>&1 | Select-Object -Last 2
if ($LASTEXITCODE -ne 0) { throw 'd8 failed' }
java -cp $jar com.android.tools.smali.baksmali.Main d "$work\dexout\classes.dex" -o "$work\helper" -a 21 2>&1 | Out-Null
if (-not (Test-Path "$work\helper\com\ss\view\RoundScreenInsets.smali")) { throw 'helper smali missing' }

# ---------- 2) baksmali original dexes ----------
"=== [3] extract + baksmali dexes ==="
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead("$w\squarehome-orig.apk")
$map = [ordered]@{ 'classes.dex' = 'smali_cls'; 'classes2.dex' = 'smali_cls2'; 'classes4.dex' = 'smali_cls4' }
foreach ($k in $map.Keys) {
    $e = $z.Entries | Where-Object { $_.FullName -eq $k }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, "$work\base\$k", $true)
}
$z.Dispose()
foreach ($k in $map.Keys) {
    $dir = "$work\$($map[$k])"
    Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
    java -cp $jar com.android.tools.smali.baksmali.Main d "$work\base\$k" -o $dir -a 21 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "baksmali $k failed" }
}

# ---------- 3) hooks ----------
"=== [4] insert hooks ==="

# (a) round-screen insets, recomputed on every scroll  (classes.dex)
$f = "$work\smali_cls\com\ss\view\AnimateGridView`$a.smali"
Insert-Before $f `
    "    invoke-static {v0}, Lcom/ss/view/AnimateGridView;->a(Lcom/ss/view/AnimateGridView;)Landroid/widget/AbsListView`$OnScrollListener;" `
    "    # >>> DouqiuOS hook: round-screen insets (per scroll)
    iget-object v0, p0, Lcom/ss/view/AnimateGridView`$a;->e:Lcom/ss/view/AnimateGridView;

    invoke-static {v0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V

    invoke-static {v0}, Lcom/ss/view/AnimateGridView;->a(Lcom/ss/view/AnimateGridView;)Landroid/widget/AbsListView`$OnScrollListener;" `
    "insets-onScroll"

# (b) animation speed for the elastic bounce animation  (classes.dex)
Insert-Before $f `
    "    invoke-virtual {v0, v1}, Landroid/view/View;->startAnimation(Landroid/view/animation/Animation;)V" `
    "    # >>> DouqiuOS hook: animation speed (elastic bounce)
    invoke-static {v1}, Lcom/ss/view/RoundScreenInsets;->scaleAnimation(Landroid/view/animation/Animation;)V" `
    "anim-elastic"

# (c) round-screen insets after layout + (d) animation speed for drawer items  (classes2.dex)
$f2 = "$work\smali_cls2\com\ss\view\AnimateGridView.smali"
Insert-Before $f2 `
    "    invoke-super/range {p0 .. p5}, Landroid/widget/GridView;->onLayout(ZIIII)V" `
    "    invoke-super/range {p0 .. p5}, Landroid/widget/GridView;->onLayout(ZIIII)V

    # >>> DouqiuOS hook: round-screen insets (after layout)
    invoke-static {p0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V" `
    "insets-onLayout"

Insert-Before $f2 `
    "    invoke-virtual {v2, v1}, Landroid/view/View;->startAnimation(Landroid/view/animation/Animation;)V" `
    "    # >>> DouqiuOS hook: animation speed (drawer items)
    invoke-static {v1}, Lcom/ss/view/RoundScreenInsets;->scaleAnimation(Landroid/view/animation/Animation;)V" `
    "anim-item"

# (e) live wallpaper: skip the app's own wallpaper drawing  (classes4.dex)
$f4 = "$work\smali_cls4\com\ss\squarehome2\fk.smali"
Insert-Before $f4 `
    "    sget-object v0, Lcom/ss/squarehome2/fk;->b:Landroid/app/WallpaperManager;" `
    "    # >>> DouqiuOS hook: live wallpaper -> skip app-drawn wallpaper
    invoke-static {}, Lcom/ss/view/RoundScreenInsets;->skipWallpaper()Z

    move-result v0

    if-nez v0, :douqiu_draw_wp

    return-void

    :douqiu_draw_wp
    sget-object v0, Lcom/ss/squarehome2/fk;->b:Landroid/app/WallpaperManager;" `
    "lwp-skip"

Copy-Item "$work\helper\com\ss\view\RoundScreenInsets.smali" "$work\smali_cls2\com\ss\view\RoundScreenInsets.smali" -Force

# ---------- 4) assemble ----------
"=== [5] assemble ==="
foreach ($k in $map.Keys) {
    java -cp $jar com.android.tools.smali.smali.Main a "$work\$($map[$k])" -o "$work\patched\$k" -a 21 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "assemble $k failed" }
}
Get-ChildItem "$work\patched" | Select-Object Name, Length | Format-Table -AutoSize

"=== [6] verify ==="
foreach ($k in $map.Keys) {
    $a = & $dd -f "$work\base\$k" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size'
    $b = & $dd -f "$work\patched\$k" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size'
    "  $k base   : " + (($a | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
    "  $k patched: " + (($b | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
}
$txt = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes("$work\patched\classes4.dex"))
"  classes4 skipWallpaper call present: " + $txt.Contains('skipWallpaper')
