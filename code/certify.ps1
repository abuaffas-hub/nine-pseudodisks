# Certify the 584 canonical cubes on Windows (PowerShell).
# For each cube: write a standalone CNF (gen_cnf.py), solve it with CaDiCaL producing an LRAT
# proof, check the proof with lrat-check, record the result, delete the large files.
#
#   powershell -ExecutionPolicy Bypass -File certify.ps1 -Test          # one easy cube, shows logs
#   powershell -ExecutionPolicy Bypass -File certify.ps1 -Workers 4     # all cubes (resumable)
#   powershell -ExecutionPolicy Bypass -File certify.ps1 -Status        # progress
#
# Options: -Python py   (if 'python' is not recognized)
#          -Tools  DIR  (folder with cadical.exe and lrat-check.exe; default $HOME\nine_tools)
#          -Keep        (keep CNF and proof files in proofs\)
#
# The solver and checker output of every cube is kept in checklogs\ (also after success).
# A cube counts as certified only if CaDiCaL exits with code 20 and prints 's UNSATISFIABLE',
# and lrat-check exits with code 0 and prints 'VERIFIED' (not 'NOT VERIFIED').
# Tools: CaDiCaL 3.0.1 (tag rel-3.0.1) and lrat-check from drat-trim commit 2e3b2dc; see README.
param(
  [int]$Workers = 0,
  [int]$Worker = -1,
  [switch]$Test,
  [switch]$Status,
  [switch]$Keep,
  [string]$Python = "python",
  [string]$Tools = "$HOME\nine_tools"
)
Set-Location $PSScriptRoot
$Cadical = Join-Path $Tools "cadical.exe"
$Checker = Join-Path $Tools "lrat-check.exe"
New-Item -ItemType Directory -Force work, proofs, checklogs | Out-Null

function Get-Verified {
  $s = @{}
  Get-ChildItem certified_*.txt -ErrorAction SilentlyContinue | ForEach-Object {
    Get-Content $_.FullName | ForEach-Object {
      if ($_ -match '^cube (\d+) VERIFIED') { $s[[int]$Matches[1]] = $true }
    }
  }
  return $s
}

function Invoke-Cube([int]$ci, [string]$tag, [bool]$show) {
  $d = Join-Path "work" "c$ci"
  New-Item -ItemType Directory -Force $d | Out-Null
  $cnf = Join-Path $d "cube.cnf"; $prf = Join-Path $d "proof.lrat"
  & $Python gen_cnf.py $ci $cnf
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $cnf)) {
    Add-Content "failures_$tag.txt" "cube $ci GEN_FAILED"; return }
  $h = (Get-FileHash $cnf -Algorithm SHA256).Hash
  $t0 = Get-Date
  $solve = (& $Cadical -q --lrat=1 --binary=0 $cnf $prf 2>&1 | Out-String); $src = $LASTEXITCODE
  $t1 = Get-Date
  Set-Content (Join-Path $d "solve.log") $solve
  Set-Content (Join-Path "checklogs" "cube$ci.solve.log") $solve
  if ($show) { Write-Host "--- cadical output:"; Write-Host $solve }
  if ($src -ne 20 -or $solve -notmatch '(?m)^s UNSATISFIABLE') {
    Add-Content "failures_$tag.txt" "cube $ci SOLVER_DID_NOT_REPORT_UNSAT"; return }
  $psize = (Get-Item $prf).Length
  $check = (& $Checker $cnf $prf 2>&1 | Out-String); $crc = $LASTEXITCODE
  $t2 = Get-Date
  Set-Content (Join-Path $d "check.log") $check
  Set-Content (Join-Path "checklogs" "cube$ci.check.log") $check
  if ($show) { Write-Host "--- lrat-check output:"; Write-Host $check }
  if ($crc -eq 0 -and $check -match 'VERIFIED' -and $check -notmatch 'NOT VERIFIED') {
    $ts = [int]($t1 - $t0).TotalSeconds; $tc = [int]($t2 - $t1).TotalSeconds
    Add-Content "certified_$tag.txt" "cube $ci VERIFIED mode=lrat solve=${ts}s check=${tc}s proof=${psize}B cnf_sha256=$h"
    if ($Keep) { Move-Item $cnf "proofs\cube$ci.cnf" -Force; Move-Item $prf "proofs\cube$ci.lrat" -Force }
    Remove-Item -Recurse -Force $d
  } else {
    Add-Content "failures_$tag.txt" "cube $ci CHECK_FAILED"
  }
}

if ($Status) {
  $v = (Get-Verified).Count
  $f = 0; Get-ChildItem failures_*.txt -ErrorAction SilentlyContinue | ForEach-Object { $f += @(Get-Content $_.FullName).Count }
  $w = @(Get-ChildItem work -Directory -Filter "c*" -ErrorAction SilentlyContinue).Count
  Write-Host "verified: $v / 584    failures: $f    in progress: $w"
  if ($f -gt 0) { Get-ChildItem failures_*.txt | ForEach-Object { Get-Content $_.FullName | Select-Object -Last 5 } }
  if ($v -eq 584) { Write-Host "ALL 584 CUBES CERTIFIED" }
  exit 0
}

foreach ($exe in @($Cadical, $Checker)) {
  if (-not (Test-Path $exe)) { Write-Host "missing $exe"; exit 1 }
}

if ($Test) {
  Invoke-Cube 350 "test" $true
  Write-Host "--- result:"
  Get-Content certified_test.txt -ErrorAction SilentlyContinue | Select-Object -Last 1
  Get-Content failures_test.txt -ErrorAction SilentlyContinue
  exit 0
}

if ($Worker -ge 0) {
  # worker mode: process every Workers-th remaining cube
  $todo = @(Get-Content (Join-Path "work" "todo.txt") | ForEach-Object { [int]$_ })
  for ($i = $Worker; $i -lt $todo.Count; $i += $Workers) { Invoke-Cube $todo[$i] "w$Worker" $false }
  exit 0
}

# launcher
if ($Workers -le 0) { $Workers = [Math]::Max(1, [Environment]::ProcessorCount - 2) }
& $Python gen_cnf.py 350 (Join-Path "work" "warmup.cnf") | Out-Null   # builds base_pseudo.pkl once
Remove-Item (Join-Path "work" "warmup.cnf") -ErrorAction SilentlyContinue
$done = Get-Verified
$all = & $Python gen_cnf.py --list | ForEach-Object { [int]$_ }
$todo = @($all | Where-Object { -not $done.ContainsKey($_) })
Set-Content (Join-Path "work" "todo.txt") ($todo -join "`n")
Write-Host "$($todo.Count) cubes to certify with $Workers workers"
for ($k = 0; $k -lt $Workers; $k++) {
  $argline = "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -Worker $k -Workers $Workers -Python $Python -Tools `"$Tools`""
  if ($Keep) { $argline += " -Keep" }
  Start-Process powershell -ArgumentList $argline -WindowStyle Minimized
}
Write-Host "started $Workers minimized worker windows; check progress with:"
Write-Host "  powershell -ExecutionPolicy Bypass -File certify.ps1 -Status"
