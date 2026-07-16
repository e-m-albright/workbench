# Testing a Skill

## Test cases

After drafting, write 2-3 realistic test prompts — what a real user would actually say. Save to `evals/evals.json` if you want structured tests:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column for profit margin. Revenue in C, costs in D",
      "expected_output": "Spreadsheet with new column showing profit margin %",
      "files": [],
      "expectations": ["Output is a .xlsx file", "Includes new column with profit margin formula"]
    }
  ]
}
```

See [schemas.md](schemas.md) for the full schema (used by Anthropic's eval runner; we don't currently run it but the schema is the data contract for any future eval system we add).

**Bad test prompts:** "Format this data." "Extract text from PDF." Too abstract — won't reliably trigger or test anything.

**Good test prompts:** Concrete, specific, with file paths, column names, casual tone, real backstory. See the example above.

## Trigger queries

To validate the description triggers correctly without false positives, write 8-10 should-trigger prompts and 8-10 should-not-trigger near-misses. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Negative cases must be **near-misses** — share keywords with the skill but actually need something else. Obvious irrelevance (e.g. "write a fibonacci function" for a PDF skill) tests nothing.

## Manual validation

If you don't have an eval runner, just do it manually:
1. Spawn a subagent with the skill loaded; give it a test prompt.
2. Spawn another subagent **without** the skill; same prompt.
3. Compare outputs.
4. Read both transcripts — note where the skill helped, where it confused the agent, where rote instructions made the agent waste time.

Alternatively, just describe each test case to yourself and see what Claude with the skill produces vs. what Claude without the skill produces. Less rigorous; works fine for low-stakes iteration.
