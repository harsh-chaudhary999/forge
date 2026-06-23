# Performance Budget — Core Web Vitals & Optimization

Define measurable performance targets:

- **Largest Contentful Paint (LCP)** - Target: <2.5s
- **Interaction to Next Paint (INP)** — primary Core Web Vital (replaced FID Mar 2024). Target: ≤200ms ("good"). (FID is legacy; its old target was ≤100ms.)
- **Cumulative Layout Shift (CLS)** - Target: <0.1
- **Initial page load time** - Target (depends on feature)
- **Bundle size** - Frontend code target (depends on feature)
- **Time to Interactive (TTI)** - Target: <3.5s
- **JavaScript parse/compile time** - Constraint on feature code

Considerations:
- Code splitting strategy
- Image optimization
- Third-party script impact
- Resource hints (preload, prefetch)
- Caching strategy
