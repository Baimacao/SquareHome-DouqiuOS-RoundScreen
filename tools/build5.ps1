#!/usr/bin/env pwsh
# Build patched dexes (v11): ONLY the round-screen insets hooks (2), no wallpaper / no animation hooks.
# ASCII-only (PS 5.1 reads .ps1 as ANSI without BOM).
$ErrorActionPreference = 'Continue'
$w = 'E:\B1807\Documents\DSH\squarehome-mod'
$jar = "$w\_tools\lib\apktool-cli-3.0.3.jar"
$aj = 'E:\B1807\Documents\DSH\sdk\platform\android.jar'
$d8 = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\d8.bat'
$work = "$w\work3"
New-Item -ItemType Directory -Force -Path "$work\base","$work\classes","$work\helper","$work\patched" | Out-Null

function Insert-InMethod($path, $methodDecl, $anchor, $insert, $tag) {
    $t = Get-Content $path -Raw -Encoding utf8
    $i = $t.IndexOf($methodDecl)
    if ($i -lt 0) { throw "method [$methodDecl] not found in $path" }
    $j = $t.IndexOf(".end method", $i)
    if ($j -lt 0) { throw "end of method not found for [$tag]" }
    $body = $t.Substring($i, $j - $i)
    $k = $body.IndexOf($anchor)
    if ($k -lt 0) { throw "anchor [$tag] not found inside $methodDecl" }
    $nb = $body.Substring(0, $k) + $insert.TrimEnd("`r", "`n") + "`n`n" + $body.Substring($k)
    $t = $t.Substring(0, $i) + $nb + $t.Substring($j)
    [System.IO.File]::WriteAllText($path, $t, (New-Object System.Text.UTF8Encoding($false)))
    "  hook [$tag] -> $methodDecl"
}

"=== [1] javac RoundScreenInsets ==="
Remove-Item -Recurse -Force "$work\classes" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\classes" | Out-Null
javac --release 11 -nowarn -cp $aj -d "$work\classes" "$w\src\com\ss\view\RoundScreenInsets.java" 2>&1
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }

"=== [2] d8 + baksmali helper ==="
Remove-Item -Recurse -Force "$work\dexout","$work\helper" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\dexout" | Out-Null
$cls = Get-ChildItem "$work\classes\com\ss\view\*.class" | ForEach-Object { $_.FullName }
& $d8 --min-api 21 --output "$work\dexout" $cls 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'd8 failed' }
java -cp $jar com.android.tools.smali.baksmali.Main d "$work\dexout\classes.dex" -o "$work\helper" -a 21 2>&1 | Out-Null
Get-ChildItem "$work\helper\com\ss\view" | Select-Object -ExpandProperty Name

"=== [3] baksmali original dexes ==="
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead("$w\squarehome-orig.apk")
$map = [ordered]@{ 'classes.dex' = 'smali_cls'; 'classes2.dex' = 'smali_cls2' }
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

"=== [4] insert hooks (method scoped, 2 total) ==="
$fa = "$work\smali_cls\com\ss\view\AnimateGridView`$a.smali"
$fg = "$work\smali_cls2\com\ss\view\AnimateGridView.smali"

Insert-InMethod $fa ".method public onScroll(Landroid/widget/AbsListView;III)V" `
    "    invoke-static {v0}, Lcom/ss/view/AnimateGridView;->a(Lcom/ss/view/AnimateGridView;)Landroid/widget/AbsListView`$OnScrollListener;" `
    "    # >>> DouqiuOS hook: round-screen insets (per scroll)
    iget-object v0, p0, Lcom/ss/view/AnimateGridView`$a;->e:Lcom/ss/view/AnimateGridView;

    invoke-static {v0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V

    invoke-static {v0}, Lcom/ss/view/AnimateGridView;->a(Lcom/ss/view/AnimateGridView;)Landroid/widget/AbsListView`$OnScrollListener;" `
    "insets-onScroll"

Insert-InMethod $fg ".method protected onLayout(ZIIII)V" `
    "    invoke-super/range {p0 .. p5}, Landroid/widget/GridView;->onLayout(ZIIII)V" `
    "    invoke-super/range {p0 .. p5}, Landroid/widget/GridView;->onLayout(ZIIII)V

    # >>> DouqiuOS hook: round-screen insets (after layout)
    invoke-static {p0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V" `
    "insets-onLayout"

Get-ChildItem "$work\helper\com\ss\view\*.smali" | ForEach-Object {
    Copy-Item $_.FullName "$work\smali_cls2\com\ss\view\$($_.Name)" -Force
    "  helper copied: $($_.Name)"
}

"=== [5] assemble ==="
foreach ($k in $map.Keys) {
    java -cp $jar com.android.tools.smali.smali.Main a "$work\$($map[$k])" -o "$work\patched\$k" -a 21 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "assemble $k failed" }
}
Get-ChildItem "$work\patched" | Select-Object Name, Length | Format-Table -AutoSize

"=== [6] check ==="
$data = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes("$work\patched\classes.dex"))
"  classes.dex has applyToGridView: " + $data.Contains('applyToGridView')
$data2 = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes("$work\patched\classes2.dex"))
"  classes2.dex has applyToGridView: " + $data2.Contains('applyToGridView') + " | skipWallpaper: " + $data2.Contains('skipWallpaper')
