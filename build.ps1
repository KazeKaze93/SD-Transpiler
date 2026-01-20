if (Test-Path "dist")
{
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "build")
{
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "launcher.py")
{
    Remove-Item -Force "launcher.py"
}

Write-Host "--- Activating VENV ---" -ForegroundColor Cyan
.\.venv\Scripts\activate.ps1

pip install pyinstaller --quiet

Write-Host "--- Creating Launcher ---" -ForegroundColor Cyan
Set-Content -Path "launcher.py" -Value "from src.main import main; main()"

Write-Host "--- Building EXE ---" -ForegroundColor Green

pyinstaller --noconsole --onefile --name "SD-Transpiler" `
    --add-data "src/data;data" `
    --collect-all qt_material `
    --hidden-import PyQt5.sip `
    --hidden-import PyQt5.QtSvg `
    launcher.py

if (Test-Path "launcher.py")
{
    Remove-Item -Force "launcher.py"
}
if (Test-Path "SD-Transpiler.spec")
{
    Remove-Item -Force "SD-Transpiler.spec"
}

Write-Host "--- DONE! Launch dist/SD-Transpiler.exe ---" -ForegroundColor Yellow