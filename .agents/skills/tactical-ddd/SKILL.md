---
name: tactical-ddd
description: Detects anemic domain models, validates and refactors them into rich domain models, and enforces tactical DDD patterns (Entities, Value Objects, Aggregates, Domain Services, Domain Events, Ports & Adapters). Use when the user asks to validate domain models, refactor domain objects, or structure hexagonal domain layers.
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 1.0.0
---

# Tactical DDD — Rich Domain Modeling

## Core Building Blocks

| Pattern | Definition | Key Rules |
| :--- | :--- | :--- |
| **Entity** | Has unique identity tracked over time | Must validate own invariants on construction and mutation |
| **Value Object** | Identity defined solely by its values (immutable) | Replace, never mutate; self-validating |
| **Aggregate Root** | Cluster of domain objects treated as a single transactional unit | External objects only reference the Root; enforces all multi-entity invariants |
| **Domain Service** | Pure business logic that spans multiple aggregates | Stateless, named after domain verbs, no infra code |
| **Port (Interface)** | Boundary contract in the application layer | Inbound (Use Cases) and Outbound (Gateways/Repositories) |

## Hexagonal Boundary Rules
1. Domain NEVER imports application or adapters.
2. Application NEVER imports concrete adapters.
3. Adapters implement outbound ports and invoke inbound ports.
