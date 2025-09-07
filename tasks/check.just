# run check tasks
[group('check')]
check: check-code check-type check-format check-test

# check code quality
[group('check')]
check-code:
    uv run ruff check {{SOURCES}} {{TESTS}}

# check code format
[group('check')]
check-format:
    uv run ruff format --check {{SOURCES}} {{TESTS}}

# check unit tests
[group('check')]
check-test:
    uv run pytest {{TESTS}}

# check code typing
[group('check')]
check-type:
    uv run ty check {{SOURCES}} {{TESTS}}


