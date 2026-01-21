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
    Write-Error "Virtual environment not found! Run 'python -m venv .venv'"
    exit 1
}
.\.venv\Scripts\activate.ps1

# --- Dependencies ---
Write-Host "--- Installing Build Tools ---" -ForegroundColor Cyan
pip install pyinstaller pywin32 --quiet

# --- Building ---
Write-Host "--- Building EXE (PyQt6 + DPAPI) ---" -ForegroundColor Green

pyinstaller --noconsole --onefile --name "SD-Transpiler" `
    --add-data "src/data;data" `
    --collect-all qt_material `
    --hidden-import "PyQt6" `
    --hidden-import "win32timezone" `
    --hidden-import "win32crypt" `
    --clean `
    main.py

Write-Host "--- DONE! Artifact: dist/SD-Transpiler.exe ---" -ForegroundColor Yellow