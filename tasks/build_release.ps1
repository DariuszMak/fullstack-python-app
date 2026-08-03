docker-compose run --build app ; 

docker-compose run app sh -c "dos2unix thorough.env src/backend/openmeteo/places/places.json src/ui/react_ui/frontend/frontend_test.sh" ; 
docker-compose run app sh -c "cd src/ui/react_ui/frontend && rm -rf node_modules package-lock.json && npm install && cd /app && uv sync --dev --locked --no-cache && chmod +x src/ui/react_ui/frontend/frontend_test.sh && src/ui/react_ui/frontend/frontend_test.sh && uv run pytest tests/ --cov=src"
docker-compose run --rm --remove-orphans app sh -c "uv sync --dev --locked --no-cache && uv run pyinstaller --clean ./scripts/standalone_build_linux.spec && cp -r dist/* releases/linux/" ; 
Remove-Item -r -fo .\dist, .\build, .\linux ; 


Set-Location src\ui\react_ui\frontend ; 
if (Test-Path node_modules) {
    Remove-Item -Recurse -Force node_modules
}
Remove-Item package-lock.json ; 
npm cache clean --force ; 
npm install ; 
Set-Location (git rev-parse --show-toplevel)

uv sync --dev --no-cache --locked ; 

.\scripts\format_and_lint.ps1 ; 
.\src\ui\react_ui\frontend\frontend_format_and_lint.ps1 ; 

uv run pyinstaller --clean .\scripts\standalone_build_windows.spec ; 

Copy-Item -r -fo .\dist\* .\releases\windows\ ; 
Remove-Item -r -fo .\dist, .\build ; 


uv sync --dev --locked --no-cache ; 