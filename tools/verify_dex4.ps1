#!/usr/bin/env pwsh
# Final verification for the v2 build: smali diff (minimal patch) + APK integrity
$ErrorActionPreference = 'Stop'
$w = 'E:\B1807\Documents\DSH\squarehome-mod'
$jar = "$w\_tools\lib\apktool-cli-3.0.3.jar"
$final = "$w\SquareHome_3.0.1_round-v4.apk"
$v = "$w\work3\verify4"
New-Item -ItemType Directory -Force -Path $v | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem
function Get-Entry($apk, $name, $out) {
    $z = [System.IO.Compression.ZipFile]::OpenRead($apk)
    $e = $z.Entries | Where-Object { $_.FullName -eq $name }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, $out, $true)
    $z.Dispose()
}

foreach ($n in @('classes','classes2')) {
    Get-Entry "$w\squarehome-orig.apk" "$n.dex" "$v\orig_$n.dex"
    Get-Entry $final "$n.dex" "$v\new_$n.dex"
    foreach ($side in @('orig','new')) {
        $dir = "$v\smali_${side}_$n"
        Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
        java -cp $jar com.android.tools.smali.baksmali.Main d "$v\${side}_$n.dex" -o $dir -a 21 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "baksmali ${side}_$n failed" }
    }
}

"=== smali diff (original APK vs patched APK) ==="
foreach ($n in @('classes','classes2')) {
    $a = "$v\smali_orig_$n"; $b = "$v\smali_new_$n"
    $fa = Get-ChildItem $a -Recurse -File | ForEach-Object { $_.FullName.Substring($a.Length + 1) }
    $fb = Get-ChildItem $b -Recurse -File | ForEach-Object { $_.FullName.Substring($b.Length + 1) }
    "---- $n : orig=$($fa.Count) new=$($fb.Count) ----"
    foreach ($f in (Compare-Object $fa $fb)) {
        if ($f.SideIndicator -eq '=>') { "  [ADDED]   $($f.InputObject)" } else { "  [REMOVED] $($f.InputObject)" }
    }
    foreach ($f in $fa) {
        if ($fb -notcontains $f) { continue }
        if ((Get-Content (Join-Path $a $f) -Raw) -ne (Get-Content (Join-Path $b $f) -Raw)) { "  [CHANGED] $f" }
    }
}

