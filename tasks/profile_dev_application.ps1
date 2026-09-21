Write-Host "Starting application with py-spy profiling..."

uv run py-spy record -o profile.svg -- python -m src.main

Write-Host "Profiling complete! Saved to profile.svg"

# uv run scalene run --malloc-threshold 1 --cpu-percent-threshold 0 --profile-all .\src\main.py

# uv run scalene view --standalone
# Start-Process .\scalene-profile.html ; 
