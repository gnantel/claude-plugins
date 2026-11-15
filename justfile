# Run the unit tests (pytest is fetched on demand by uvx).
test *args:
    PYTHONDONTWRITEBYTECODE=1 uvx pytest {{args}}
