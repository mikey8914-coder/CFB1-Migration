# CFB1 Migration

Migration of the CFB1 college football model from Google Colab into a maintainable Python project.

Initial goals:
- Preserve existing CFB1 model logic.
- Remove normal Odds API dependency from CFB1.
- Use Action Network first and Covers as gap-fill for spread and game total.
- Keep sportsbook pricing and Odds API usage primarily with Bet Slip Architect.
- Validate migrated outputs against known Colab results before changing model logic.
