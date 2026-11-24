# Run the unit tests (pytest is fetched on demand by uvx).
test *args:
    PYTHONDONTWRITEBYTECODE=1 uvx pytest {{args}}

# Run a plugin's eval suite with and without the plugin (for example `just eval coding-standards`).
eval plugin *args:
    claude plugin eval plugins/{{plugin}} --scaffold --trust-plugin --no-publish --judge-model sonnet --allow-tools 'Bash(git:*)' 'Bash(gh:*)' 'Bash(python3:*)' Edit {{args}}
