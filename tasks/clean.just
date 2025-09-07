# run clean tasks
[group('clean')]
clean: clean-pytest clean-python clean-ruff

# clean uv lock
[confirm]
[group('clean')]
clean-lock:
    rm -rf uv.lock

# clean pytest cache
[group('clean')]
clean-pytest:
    rm -rf .pytest_cache/

# clean python caches
[group('clean')]
clean-python:
    find . -type f -name '*.py[co]' -delete
    find . -type d -name __pycache__ -exec rm -r {} \+

# clean ruff cache
[group('clean')]
clean-ruff:
    rm -rf .ruff_cache/

# clean venv folder
[confirm]
[group('clean')]
clean-venv:
    rm -rf .venv/
