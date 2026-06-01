<#
.SYNOPSIS
  MiniCompiler: Final Defense Demo (Tests + Live Compilation + ASM Output)
.DESCRIPTION
  Runs full test suite, shows summary, compiles demo, prints generated ASM, then runs executable.
#>
[CmdletBinding()]
param()

$Host.UI.RawUI.WindowTitle = "MiniCompiler Final Demo"
Set-Location $PSScriptRoot

# Colors
$C = @{ B="Cyan"; G="Green"; R="Red"; Y="Yellow"; GR="Gray"; W="White" }

Write-Host "`n========================================================" -ForegroundColor $C.B
Write-Host "   MiniCompiler: Final Defense Demo" -ForegroundColor $C.B
Write-Host "========================================================`n" -ForegroundColor $C.B

# =========================================================
# PART 1: FULL TEST SUITE
# =========================================================
Write-Host "[1/3] Running Full Test Suite (Lexer -> Codegen)..." -ForegroundColor $C.GR
Write-Host "--------------------------------------------------------" -ForegroundColor $C.GR

& python run_all_tests.py
$testCode = $LASTEXITCODE

Write-Host "--------------------------------------------------------" -ForegroundColor $C.GR
Write-Host "`n--- TEST SUITE SUMMARY ---" -ForegroundColor $C.B
if ($testCode -eq 0) {
    Write-Host "  ✅ ALL 6 MODULES PASSED" -ForegroundColor $C.G
    Write-Host "  Lexer      | Parser     | Semantic   | IR         | ControlFlow| Codegen" -ForegroundColor $C.GR
} else {
    Write-Host "  ⚠️  SOME MODULES REPORTED ISSUES" -ForegroundColor $C.Y
    Write-Host "  (Proceeding to live compilation demo...)" -ForegroundColor $C.GR
}
Write-Host ""

# =========================================================
# PART 2: LIVE COMPILATION
# =========================================================
Write-Host "[2/3] Live Compilation: examples/demo_final.src" -ForegroundColor $C.GR
$DemoSrc = "examples/demo_final.src"
$TempDir = Join-Path $PSScriptRoot "build_demo"
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Path $TempDir | Out-Null

$Asm = Join-Path $TempDir "demo.asm"
$Obj = Join-Path $TempDir "demo.obj"
$Exe = Join-Path $TempDir "demo.exe"

# Activate venv if present
if (Test-Path ".\venv\Scripts\Activate.ps1") { & ".\venv\Scripts\Activate.ps1" > $null }

# Compile
$compileArgs = @("-m", "src.main", "compile", "--input", $DemoSrc, "--output", $Asm, "--verbose")
$compOutput = & python $compileArgs 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Compilation failed!" -ForegroundColor $C.R
    exit 1
}

# Print pipeline stages
Write-Host "`n--- Compilation Pipeline ---" -ForegroundColor $C.B
$compOutput -split "`n" | ForEach-Object {
    $line = $_.Trim()
    if ($line -match "\[LEX\]|\[PARSE\]|\[SEMANTIC\]|\[IR\]|\[SUCCESS\]") {
        Write-Host "  $line" -ForegroundColor $C.GR
    }
}

# NASM
Write-Host "  [NASM] Assembling... " -NoNewline
& nasm -f win64 $Asm -o $Obj 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor $C.R; exit 1 }
Write-Host "OK" -ForegroundColor $C.G

# GCC
Write-Host "  [GCC]  Linking...     " -NoNewline
& gcc -o $Exe $Obj 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor $C.R; exit 1 }
Write-Host "OK" -ForegroundColor $C.G

#  DISPLAY GENERATED ASSEMBLY
Write-Host "`n--- Generated Assembly Code ---" -ForegroundColor $C.B
if (Test-Path $Asm) {
    Get-Content $Asm | ForEach-Object { Write-Host "  $_" -ForegroundColor $C.GR }
} else {
    Write-Host "  (Assembly file not found)" -ForegroundColor $C.Y
}
Write-Host ""

# =========================================================
# PART 3: EXECUTION & FINAL
# =========================================================
Write-Host "[3/3] Executing Program..." -ForegroundColor $C.GR
& $Exe | Out-Null
$exitCode = $LASTEXITCODE

Write-Host "`n--- FINAL RESULT ---" -ForegroundColor $C.B
Write-Host "  Program Exit Code: $exitCode" -ForegroundColor $C.W
if ($exitCode -eq 180) {
    Write-Host "  Status: SUCCESS (Expected: 180)" -ForegroundColor $C.G
} else {
    Write-Host "  Status: UNEXPECTED (Expected: 180)" -ForegroundColor $C.R
}

# Cleanup
Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
Write-Host "`n Demo Complete. Ready for defense.`n" -ForegroundColor $C.G

exit $(if ($exitCode -eq 180 -and $testCode -eq 0) { 0 } else { 1 })