uv run ruff format src tests --exclude 'moc_.*\.py|files_rc\.py'
uv run ruff check --fix src tests --exclude 'moc_.*\.py|files_rc\.py'
uv run ruff check --fix --unsafe-fixes src tests --exclude 'moc_.*\.py|files_rc\.py'
uv run ruff check --fix --select I src tests --exclude 'moc_.*\.py|files_rc\.py'

uv run pip-audit
uv run ruff check src tests --exclude 'moc_.*\.py|files_rc\.py'
uv run ruff format --check src tests --exclude 'moc_.*\.py|files_rc\.py'

uv run ruff check src tests --output-format json > ruff-report.json

uv run vulture src tests --exclude "src/ui/pyside_ui/forms" --min-confidence 80

uv run mypy --strict src tests --exclude 'moc_.*\.py|files_rc\.py'

# uv run mypy --explicit-package-bases src tests --exclude 'moc_.*\.py|files_rc\.py'
# uv run mypy --explicit-package-bases --check-untyped-defs src tests --exclude 'moc_.*\.py|files_rc\.py'
# uv run mypy --strict src tests

uv run lint-imports --config pyproject.toml

uv run semgrep --config=auto --config=p/security-audit --error src tests

uv run coverage report
uv run coverage xml