# CFB1 Migration Plan

## Project principles

1. Preserve existing CFB1 quantitative logic before refactoring.
2. The current Google Colab notebook is the reference implementation.
3. CFB1 should not normally use The Odds API.
4. CFB1 market inputs are spread and game total only.
5. Market acquisition priority is Action Network first, then Covers as gap-fill. Missing games may be excluded rather than aggressively searched.
6. Exact sportsbook prices, props, promos, and Odds API usage belong primarily to Bet Slip Architect.
7. Migrated outputs must be validated against known historical Colab outputs before model logic changes.
8. Do not create new handicapping logic during migration.
9. Python remains the source of truth for CFB1 deterministic outputs.
10. Keep external-data acquisition separate from model logic.

## Repository structure

- `legacy/`: the reference Colab notebook and original implementation artifacts.
- `docs/`: migration documentation.
- `src/`: future Python implementation.
- `data/market/`: market input data.
- `data/bcf/`: BCF input data.
- `data/outputs/`: deterministic model outputs and historical comparison artifacts.
- `tests/`: future validation against known historical Colab outputs.

This initial scaffold contains no model implementation or dependencies.
