CURRENT_DIR="$(pwd)"
cd "$(dirname "$0")"

npx vitest run

cd "$CURRENT_DIR"