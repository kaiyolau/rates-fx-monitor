# Project rules for AI assistants

Rates & FX Monitor: a Python + DuckDB pipeline writes `web/public/data.json`; a static
React page reads it. No backend, no database server.

## Rules

- **Never edit a test just to make it pass.** If a test fails, fix the code, or explain why the
  test is wrong and ask before changing it.
- **Keep SQL readable.** One query per file in `pipeline/sql/`, a header comment saying what it
  checks and its thresholds, CTEs with plain names, no clever tricks. Transforms and
  data-quality rules belong in SQL, not Python.
- **Ask before adding a dependency** (Python or npm). Prefer the standard library.
- **Run the tests before saying done:** `python -m pytest -q` and `cd web && npm test && npm run build`.
- Be polite to the Valet API: one request per run, retries with backoff, no loops of calls.
  Tests use fixture data, never the live API.
- The page must work with no API key. Any number in AI-written text must pass the grounding
  check in `pipeline/summary.py`; never weaken that check to let text through.
- Record real AI mistakes in `AI_WORKFLOW.md`. Never invent entries.

## Commands

```bash
pip install -r requirements.txt
python -m pipeline.run          # fetch, transform, write web/public/data.json
python -m pytest -q             # pipeline tests
cd web && npm install && npm run dev
```

Use `/review` (`.claude/commands/review.md`) after changing any `pipeline/sql/dq_*.sql` file.
