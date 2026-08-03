uv sync --dev --no-cache --locked ; 

.\scripts\format_and_lint.ps1 ; 
.\src\ui\react_ui\frontend\frontend_format_and_lint.ps1 ; 

uv run pyinstaller --clean .\scripts\standalone_build_windows.spec ; 

Copy-Item -r -fo .\dist\* .\releases\windows\ ; 
Remove-Item -r -fo .\dist, .\build ; 


uv sync --dev --locked --no-cache ; 