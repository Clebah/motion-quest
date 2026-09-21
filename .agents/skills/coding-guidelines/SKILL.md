---
name: coding-guidelines
description: Clean code conventions, naming rules, error handling practices, and linting guidelines for professional multi-language codebases (Python and TypeScript).
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 1.0.0
---

# Clean Coding Guidelines

## Universal Rules
1. **Explicit over Implicit:** Avoid magic numbers and hidden global state.
2. **Fail Fast:** Validate inputs and domain invariants at construction boundaries.
3. **Resilient Third-Party Integrations:** Always wrap external API calls (Gemini, cloud services) in try/catch or retry-backoff blocks with graceful fallbacks.
4. **Self-Documenting Code:** Write clear symbol names and docstrings instead of redundant inline comments.
