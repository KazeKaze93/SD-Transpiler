# --- Cleanup ---
$dirs = @("dist", "build")
foreach ($d in $dirs)
{
    if (Test-Path $d)
    {
        Remove-Item -Recurse -Force $d
    }
}
$specs = Get-ChildItem -Filter "*.spec"
if ($specs)
{
    Remove-Item -Force $specs
}

# --- Environment ---
Write-Host "--- Checking VENV ---" -ForegroundColor Cyan
if (!(Test-Path ".venv"))
{
    Write-Warning "Virtual environment not found! Creating one..."
    python -m venv .venv
}

if (Test-Path ".\.venv\Scripts\Activate.ps1")
{
    . .\.venv\Scripts\Activate.ps1
}
else
{
    Write-Error "Could not activate VENV. Ensure .venv exists."
    exit 1
}

# --- Dependencies ---
Write-Host "--- Installing Dependencies ---" -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller pywin32

if (!(pip list | Select-String "qt-material"))
{
    Write-Error "CRITICAL: qt-material is NOT installed. Check requirements.txt!"
    exit 1
}

# --- Building ---
Write-Host "--- Building EXE (PyQt6 + DPAPI) ---" -ForegroundColor Green

pyinstaller --noconsole --onefile --name "SD-Transpiler" `
    --add-data "src/data;data" `
    --collect-all qt_material `
    --hidden-import "PyQt6" `
    --hidden-import "qt_material" `
    --hidden-import "win32timezone" `
    --hidden-import "win32crypt" `
    --exclude-module "PyQt5" `
    --exclude-module "PySide2" `
    --exclude-module "PySide6" `
    --clean `
    main.py

if (Test-Path "dist/SD-Transpiler.exe")
{
    Write-Host "--- SUCCESS! Artifact: dist/SD-Transpiler.exe ---" -ForegroundColor Yellow
}
else
{
    Write-Error "Build Failed! Check output above."
}