---
type: handoff
---

# Handoff: config loader refactor

## Changed Files

- src/katalint/config.py
- src/katalint/cli.py

## Commands Run

```
python -m katalint check .
```

I ran the linter locally after adjusting the default config search paths.

## Next Action

Someone should double-check the new default paths before we merge.
