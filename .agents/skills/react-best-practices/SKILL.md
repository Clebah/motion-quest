---
name: react-best-practices
description: Best practices for React component composition, hooks, rendering performance, and animation lifecycle in React and Remotion.
license: CC-BY-4.0
metadata:
  author: Tech Leads Club
  version: 1.0.0
---

# React & Remotion Best Practices

## Core Guidelines

1. **Deterministic Rendering:** Remotion renders frames frame-by-frame (`useCurrentFrame()`). Never use non-deterministic operations like `Date.now()`, `Math.random()` without seeding, or unmanaged asynchronous side-effects inside frame renders.
2. **Animation Interpolation:** Use `interpolate()` from Remotion with explicit `extrapolateLeft` and `extrapolateRight` boundaries for smooth, glitch-free transitions (Ken-Burns zoom, fade in/out).
3. **Asset Handling:** Use `<OffthreadVideo>` and `<Img>` components from Remotion for optimized headless rendering and memory management.
4. **Styling:** Prefer CSS inline styles or tailored CSS variables with backdrop filters and modern typography for rich visual aesthetics.
