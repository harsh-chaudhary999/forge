# Accessibility — WCAG 2.2 AA

Ensure WCAG 2.2 AA compliance (W3C Recommendation since Oct 2023; adds focus-not-obscured, target-size 2.5.8, dragging alternatives, accessible authentication):

- **Keyboard navigation** - All interactions keyboard accessible
- **Screen reader support** - ARIA labels, semantic HTML, roles
- **Color contrast** - WCAG AA minimum (4.5:1 for text)
- **Focus management** - Visible focus indicators, logical tab order
- **Error messages** - Associated with form fields, clear language
- **Interactive elements** - Minimum 44x44px touch targets
- **Motion** - Respect prefers-reduced-motion
- **Forms** - Labels, required indicators, validation messages

Patterns:
- Use semantic HTML (button, form, nav, main, etc)
- ARIA labels for icon buttons and dynamic content
- Focus trap in modals/dialogs
- Skip links for navigation
- Alt text for images
- Descriptive link text (not "click here")
