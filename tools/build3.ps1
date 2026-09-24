#!/usr/bin/env pwsh
# Build the patched dexes from scratch: helper (javac -> d8 -> baksmali) + 2 hooks + assemble
$ErrorActionPreference = 'Stop'
$w = 'E:\B1807\Documents\DSH\squarehome-mod'
$jar = "$w\_tools\lib\apktool-cli-3.0.3.jar"
$aj = 'E:\B1807\Documents\DSH\sdk\platform\android.jar'
$d8 = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\d8.bat'
$dd = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\dexdump.exe'
$work = "$w\work3"
New-Item -ItemType Directory -Force -Path "$work\base","$work\classes","$work\helper","$work\patched" | Out-Null

# ---------- 1) helper class ----------
"=== [1] javac RoundScreenInsets ==="
Remove-Item -Recurse -Force "$work\classes" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\classes" | Out-Null
javac --release 11 -nowarn -cp $aj -d "$work\classes" "$w\src\com\ss\view\RoundScreenInsets.java" 2>&1
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }

"=== [2] d8 -> dex ==="
Remove-Item -Recurse -Force "$work\dexout" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$work\dexout" | Out-Null
& $d8 --min-api 21 --output "$work\dexout" "$work\classes\com\ss\view\RoundScreenInsets.class" 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { throw 'd8 failed' }

"=== [3] baksmali helper ==="
Remove-Item -Recurse -Force "$work\helper" -ErrorAction SilentlyContinue
java -cp $jar com.android.tools.smali.baksmali.Main d "$work\dexout\classes.dex" -o "$work\helper" -a 21 2>&1 | Out-Null
if (-not (Test-Path "$work\helper\com\ss\view\RoundScreenInsets.smali")) { throw 'helper smali missing' }

# ---------- 2) original dexes ----------
"=== [4] extract + baksmali original dexes ==="
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead("$w\squarehome-orig.apk")
foreach ($n in @('classes.dex','classes2.dex')) {
    $e = $z.Entries | Where-Object { $_.FullName -eq $n }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, "$work\base\$n", $true)
}
$z.Dispose()
foreach ($pair in @(@('classes.dex','smali_cls'), @('classes2.dex','smali_cls2'))) {
    $dir = "$work\$($pair[1])"
    Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
    java -cp $jar com.android.tools.smali.baksmali.Main d "$work\base\$($pair[0])" -o $dir -a 21 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "baksmali $($pair[0]) failed" }
}

# ---------- 3) hooks ----------
"=== [5] insert hooks ==="
$f1 = "$work\smali_cls\com\ss\view\AnimateGridView`$a.smali"
$hook1 = @'
    # >>> DouqiuOS round-screen hook (added): re-inset list rows on every scroll
    iget-object v0, p0, Lcom/ss/view/AnimateGridView$a;->e:Lcom/ss/view/AnimateGridView;

    invoke-static {v0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V

    iget-object v0, p0, Lcom/ss/view/AnimateGridView$a;->e:Lcom/ss/view/AnimateGridView;
'@
$t1 = Get-Content $f1 -Raw -Encoding utf8
$anchor1 = "    iget-object v0, p0, Lcom/ss/view/AnimateGridView`$a;->e:Lcom/ss/view/AnimateGridView;"
if ($t1 -notmatch [regex]::Escape($anchor1)) { throw "anchor1 not found in $f1" }
$t1 = $t1.Replace($anchor1, $hook1.TrimEnd("`r","`n"))
[System.IO.File]::WriteAllText($f1, $t1, (New-Object System.Text.UTF8Encoding($false)))

$f2 = "$work\smali_cls2\com\ss\view\AnimateGridView.smali"
$t2 = Get-Content $f2 -Raw -Encoding utf8
$anchor2 = "    invoke-super/range {p0 .. p5}, Landroid/widget/GridView;->onLayout(ZIIII)V"
if ($t2 -notmatch [regex]::Escape($anchor2)) { throw "anchor2 not found in $f2" }
$hook2 = $anchor2 + @'

    # >>> DouqiuOS round-screen hook (added): inset list rows after layout
    invoke-static {p0}, Lcom/ss/view/RoundScreenInsets;->applyToGridView(Landroid/widget/GridView;)V
'@
$t2 = $t2.Replace($anchor2, $hook2.TrimEnd("`r","`n"))
[System.IO.File]::WriteAllText($f2, $t2, (New-Object System.Text.UTF8Encoding($false)))

Copy-Item "$work\helper\com\ss\view\RoundScreenInsets.smali" "$work\smali_cls2\com\ss\view\RoundScreenInsets.smali" -Force

# ---------- 4) assemble ----------
"=== [6] assemble ==="
foreach ($pair in @(@('smali_cls','classes.dex'), @('smali_cls2','classes2.dex'))) {
    java -cp $jar com.android.tools.smali.smali.Main a "$work\$($pair[0])" -o "$work\patched\$($pair[1])" -a 21 2>&1 | Select-Object -Last 4
    if ($LASTEXITCODE -ne 0) { throw "assemble $($pair[1]) failed" }
}
Get-ChildItem "$work\patched" | Select-Object Name, Length | Format-Table -AutoSize

"=== [7] verify ==="
foreach ($n in @('classes','classes2')) {
    $a = & $dd -f "$work\base\$n.dex" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size|string_ids_size'
    $b = & $dd -f "$work\patched\$n.dex" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size|string_ids_size'
    "  $n base   : " + (($a | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
    "  $n patched: " + (($b | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
}
foreach ($n in @('classes','classes2')) {
    $bytes = [System.IO.File]::ReadAllBytes("$work\patched\$n.dex")
    $txt = [System.Text.Encoding]::ASCII.GetString($bytes)
    "  $n : RoundScreenInsets=$($txt.Contains('RoundScreenInsets')) applyToGridView=$($txt.Contains('applyToGridView'))"
}
