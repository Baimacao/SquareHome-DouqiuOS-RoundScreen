#!/usr/bin/env pwsh
# Baseline round-trip test: baksmali -> smali -> dex (ASCII only, PS 5.1 safe)
$ErrorActionPreference = 'Stop'
$w = 'E:\B1807\Documents\DSH\squarehome-mod'
$jar = "$w\_tools\lib\apktool-cli-3.0.3.jar"
$work = "$w\work"
New-Item -ItemType Directory -Force -Path "$work\base","$work\rebuilt" | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead("$w\squarehome-orig.apk")
foreach ($n in @('classes.dex','classes2.dex')) {
    $e = $z.Entries | Where-Object { $_.FullName -eq $n }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, "$work\base\$n", $true)
    "extracted $n  $($e.Length) bytes  compressed=$($e.CompressedLength)"
}
$z.Dispose()

foreach ($n in @('classes','classes2')) {
    $dir = "$work\smali_$n"
    if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
    "--- baksmali $n ---"
    java -cp $jar com.android.tools.smali.baksmali.Main d "$work\base\$n.dex" -o $dir -a 21 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "baksmali $n failed" }
}
"--- assemble back ---"
foreach ($n in @('classes','classes2')) {
    java -cp $jar com.android.tools.smali.smali.Main a "$work\smali_$n" -o "$work\rebuilt\$n.dex" -a 21 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "smali $n failed" }
}
Get-ChildItem "$work\base","$work\rebuilt" -Filter *.dex | Select-Object Directory,Name,Length | Format-Table -AutoSize

"--- dexdump header check (orig vs rebuilt) ---"
$dd = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\dexdump.exe'
foreach ($n in @('classes','classes2')) {
    $a = & $dd -f "$work\base\$n.dex" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size|string_ids_size|field_ids_size|type_ids_size'
    $b = & $dd -f "$work\rebuilt\$n.dex" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size|string_ids_size|field_ids_size|type_ids_size'
    "== $n =="
    "  base   : " + (($a | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
    "  rebuilt: " + (($b | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
}
