Push-Location $PSScriptRoot

npm audit fix
npm audit --audit-level=moderate
npx --yes prettier --write .
npx --yes eslint . --fix
npx --yes tsc --noEmit
npx --yes vite build
npx knip

npm run coverage

Pop-Location