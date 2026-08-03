docker-compose run --build app ; 

docker-compose run app sh -c "dos2unix thorough.env src/backend/openmeteo/places/places.json src/ui/react_ui/frontend/frontend_test.sh" ; 
docker-compose run app sh -c "cd src/ui/react_ui/frontend && rm -rf node_modules package-lock.json && npm install && cd /app && uv sync --dev --locked --no-cache && chmod +x src/ui/react_ui/frontend/frontend_test.sh && src/ui/react_ui/frontend/frontend_test.sh && uv run pytest tests/ --cov=src"
docker-compose run --rm --remove-orphans app sh -c "uv sync --dev --locked --no-cache && uv run pyinstaller --clean ./scripts/standalone_build_linux.spec && cp -r dist/* releases/linux/" ; 
Remove-Item -r -fo .\dist, .\build, .\linux ; 