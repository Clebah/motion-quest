---
name: tlc-implement
description: 'Implement work already planned: extracts a checklist from spec/tasks, builds the code, and proves every check with tests and gates. Use when the user says "extract a checklist", "build this ticket", "implement this spec", or "tlc-implement".'
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 0.1.0
---

# TLC Implement

Extract the checks. Build. Prove each one, independently.

```
EXTRACT ─────────→ BUILD ─────────→ VERIFY
(one checklist)    (your call)      (fresh verification)
```

## Critical Rules

1. **Extract first:** Extract the exact checklist of acceptance criteria before touching code.
2. **Derive tests directly from criteria:** Every check must have a test or observable proof.
3. **Run the gate:** All tests must pass cleanly before marking a check complete.
4. **No regressions:** Ensure existing tests and contracts remain unbroken.
