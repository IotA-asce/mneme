# Context

The repository already had individual scripts for database initialization and a smoke test plus a pytest suite, but there was no single developer check command, no CI workflow, and the README did not include the full canonical setup with dev dependencies and pytest.

The project rules require clear verification before completing work. This feature makes the existing verification path repeatable locally and in GitHub Actions while keeping dependencies minimal.

GitHub Actions workflow syntax was checked against current GitHub Actions documentation before adding CI.
