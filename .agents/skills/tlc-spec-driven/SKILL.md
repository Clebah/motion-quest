---
name: tlc-spec-driven
description: Feature planning and implementation with 4 adaptive phases (Specify, Design, Tasks, Execute). Auto-sizes depth by complexity. Writes testable requirements in EARS notation, atomic tasks, atomic Conventional Commits, and requirement traceability. Features an independent Verifier, decision log (STATE.md), and quality gates. Use when (1) planning features, (2) implementing with verification and atomic commits, (3) validating an implementation against a spec. Triggers on "specify feature", "discuss feature", "design", "tasks", "implement", "validate", "verify work".
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 3.3.0
---

# Tech Lead's Club - Spec-Driven Development

Plan and implement features with precision. Granular tasks. Clear dependencies. Right tools. Zero ceremony.

```
┌──────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐
│ SPECIFY  │ → │  DESIGN  │ → │  TASKS  │ → │ EXECUTE │
└──────────┘   └──────────┘   └─────────┘   └─────────┘
   required      optional*      optional*     required

* Auto-skips when scope doesn't need it
```

## Critical Rules

1. **Tests derive from the spec's acceptance criteria** and assert spec-defined outcomes.
2. **The gate must pass (tests pass)** before a task is done — the test runner decides, not self-assessment.
3. **One atomic commit per task.** Mark the task complete in tasks list before that commit.
4. **Verifier runs automatically:** Spec-anchored outcome check with file:line evidence.
5. **Blast radius:** Local implementation only; destructive operations require explicit confirmation.

## The 4 Adaptive Phases

### Phase 1: Specify
- Define requirements using EARS notation (Easy Approach to Requirements Syntax):
  - *When [event], the system shall [action].*
  - *If [condition], the system shall [action].*
- Assign clear requirement IDs (RF-01, RF-02, etc.).
- Validate with user before moving forward.

### Phase 2: Design
- Document architecture changes, data flow, component boundaries, and contracts.
- Define data schemas (JSON, entities, interfaces).

### Phase 3: Tasks
- Break down into fine-grained atomic tasks.
- Order by dependencies.
- Define verification command for each task.

### Phase 4: Execute
- Execute task by task.
- Run tests at each step.
- Commit atomically using Conventional Commits.
