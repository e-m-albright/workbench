# Python / pytest Instantiation

The Python-specific version of the testing conventions: markers, cost tiers, and directory layout. Apply these when the project is pytest-based; other stacks should map the same ideas onto their own tooling.

## Cost-Aware Test Taxonomy

| Tier | Placement | Cost | Examples |
|------|-----------|------|----------|
| Free | Hooks + CI | $0 | Unit, contract, schema validation |
| Cheap | CI-blocking on push | ~$0.10 | Compliance, snapshot, cached API calls |
| Expensive | Release-gate / manual | ~$7+ | LLM-as-judge evals, quality/taste |
| Very Expensive | Manual only, never CI | $1+ per run | Full model-backed agent tests |

Free tests must be deterministic, fast, and make no external calls.
Cheap tests may call external APIs with mocked or cached responses.
Expensive and very expensive tests require explicit invocation.

## Pytest Marker Convention

| Marker | Meaning |
|--------|---------|
| `@pytest.mark.unit` | Deterministic, no external calls, <100ms |
| `@pytest.mark.integration` | Real dependencies (DB, API, filesystem) |
| `@pytest.mark.slow` | Exclude from default and hook runs |
| `@pytest.mark.model` | LLM-backed, manual only, costs money |
| `@pytest.mark.compliance` | Regulatory or contract tests |

Default test runs should exclude `slow` and `model`:

```ini
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-m 'not slow and not model'"
```

## Test Placement

```
tests/
  unit/          # Colocated or mirror of src structure
  integration/   # Real dependencies, network, DB
  quality/       # LLM-as-judge evals, taste tests
  model/         # Full model-backed tests (gitignore results)
```

Add `tests/model/results/` to `.gitignore` — results contain LLM output and are non-deterministic.
