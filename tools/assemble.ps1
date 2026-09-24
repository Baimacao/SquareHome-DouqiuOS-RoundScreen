#!/usr/bin/env pwsh
# Assemble patched dexes and verify the injected code is present (ASCII only)
$ErrorActionPreference = 'Stop'
$w = 'E:\B1807\Documents\DSH\squarehome-mod'
$jar = "$w\_tools\lib\apktool-cli-3.0.3.jar"
$work = "$w\work"
New-Item -ItemType Directory -Force -Path "$work\patched" | Out-Null

foreach ($n in @('classes','classes2')) {
    "--- smali a $n ---"
    java -cp $jar com.android.tools.smali.smali.Main a "$work\smali_$n" -o "$work\patched\$n.dex" -a 21 2>&1 | Select-Object -Last 4
    if ($LASTEXITCODE -ne 0) { throw "assemble $n failed" }
}
Get-ChildItem "$work\patched" | Select-Object Name, Length | Format-Table -AutoSize

"--- dex structure (base vs patched) ---"
$dd = 'E:\B1807\Documents\DSH\sdk\build-tools-r37\dexdump.exe'
foreach ($n in @('classes','classes2')) {
    $a = & $dd -f "$work\base\$n.dex" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size|string_ids_size'
    $b = & $dd -f "$work\patched\$n.dex" 2>&1 | Select-String -Pattern 'class_defs_size|method_ids_size|string_ids_size'
    "== $n =="
    "  base   : " + (($a | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
    "  patched: " + (($b | ForEach-Object { ($_ -split ':')[1].Trim() }) -join ' / ')
}

"--- string presence check ---"
foreach ($n in @('classes','classes2')) {
    $bytes = [System.IO.File]::ReadAllBytes("$work\patched\$n.dex")
    $txt = [System.Text.Encoding]::ASCII.GetString($bytes)
    $hasHelper = $txt.Contains('RoundScreenInsets')
    $hasCall = $txt.Contains('applyToGridView')
    "  $n : RoundScreenInsets=$hasHelper applyToGridView=$hasCall"
}
