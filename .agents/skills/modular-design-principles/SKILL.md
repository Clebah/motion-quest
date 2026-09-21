---
name: modular-design-principles
description: Evaluates and refactors code using core modular design principles (Acyclic Dependencies, Stable Dependencies, Single Responsibility, High Cohesion, Low Coupling). Use when designing boundaries between packages, libraries, or workers.
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 1.0.0
---

# Modular Design Principles

## Core Tenets

1. **Acyclic Dependencies Principle (ADP):** The dependency graph between packages and workers must be a Directed Acyclic Graph (DAG). Zero circular dependencies allowed.
2. **Stable Dependencies Principle (SDP):** Depend in the direction of stability. High-level policies/contracts (Domain, Manifest Schema) must not depend on volatile implementation details (Cloud SDKs, specific render engines).
3. **Common Closure Principle (CCP):** Classes and modules that change together should be packaged together.
4. **Independent Deployability / Separated Workers:** Worker boundaries communicate via contracts (`manifest.json`), ensuring each worker can be scaled, tested, and updated independently.
