---
name: tlc-plan
description: 'Turns decided work — a PRD, design doc, RFC, or thread — into tasks a builder can act on without guessing. Finds slices that each prove something, grounds them in the code, and writes intent, observable criteria with concrete values, the boundary, what the change disturbs, and only the decisions that are hard to reverse. Defaults to one task per source. Use when the user says "write the task", "cut this PRD into tasks", "turn this design doc into work", or "tlc-plan".'
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 0.2.0
---

# TLC Plan

Cut the source. Ground it in the code. Write the task.

```
CUT ──────────→ GROUND ──────────→ WRITE
(slices, then   (the repository     (one task,
 how many        it lands in)        unless a seam
 tasks)                              is forced)
```

## Critical Rules

1. Every criterion is an **observable outcome with a concrete value**.
2. **Refuse rather than guess.** A gap in the source comes back as a question.
3. `Decided` carries only what is hard to reverse, in its literal shape.
4. When the source contradicts the code, **amend the source**.
5. The task is the record of decision.

## Process

1. **Cut:** Enumerate slices. A slice is one observable outcome someone can watch work.
2. **Ground:** Map the exact files, symbols, and boundaries in the codebase that the task touches.
3. **Write:** Structure the task with:
   - Intent (what and why)
   - Observable Criteria (concrete inputs and outputs)
   - Boundaries (what is in and out of scope)
   - Gate / Test command to verify
