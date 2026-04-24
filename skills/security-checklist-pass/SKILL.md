---
name: security-checklist-pass
description: "WHEN: A feature touches auth, data handling, or external boundaries and you want a lightweight STRIDE-style checklist pass before eval or merge — no dedicated security tool required."
type: flexible
requires: [brain-read]
version: 1.0.0
preamble-tier: 3
triggers:
  - "security checklist"
  - "STRIDE pass"
  - "threat model quick"
allowed-tools:
  - Read
  - Bash
---

# security-checklist-pass

Structured **manual** checklist derived from STRIDE. Use for medium-risk changes when a full formal threat model is out of scope but "hope security is fine" is unacceptable.

## Anti-Pattern Preamble

| Rationalization | Why it fails |
|---|---|
| "We're internal-only, threats don't apply" | Insider risk, compromised laptops, and mis-scoped APIs are still threats. |
| "HTTPS means we're secure" | Transport security does not fix broken authz or IDOR. |
| "Checklist without files" | Every row must cite **where** in code or config you verified behavior. |

## STRIDE quick table

| Letter | Question | Must answer |
|--------|-----------|-------------|
| **S** Spoofing | Who can claim which identity? | AuthN mechanism + session/token lifecycle |
| **T** Tampering | Who can change data in transit or at rest? | Integrity controls, CSRF where relevant |
| **R** Repudiation | Can important actions be denied without trace? | Audit logs, request IDs |
| **I** Information disclosure | What sensitive data leaves trust boundaries? | Logs, errors, APIs, caches |
| **D** Denial of service | What can an unauthenticated caller exhaust? | Rate limits, payload size, job queues |
| **E** Elevation | Can a low-privilege role reach admin paths? | AuthZ on every route / mutation |

## OWASP-flavored add-ons (when applicable)

- [ ] **Injection:** SQL/command/template — parameterized APIs only.
- [ ] **Broken access control:** Object IDs scoped to tenant/user; admin routes gated.
- [ ] **Sensitive data:** Secrets not in repo; env vars / vault pattern documented.
- [ ] **XXE / deserialization:** Untrusted XML or pickle-style paths absent or guarded.
- [ ] **SSRF:** Server-side fetch URLs not fully attacker-controlled without allowlist.

## Output

Write a short note under the task (or brain decision) listing **Pass / Gap / N/A** per row with **file:line** evidence for any **Gap**. If any **Gap** is not fixed before merge, escalate with **`NEEDS_COORDINATION`** per **`forge-glossary`**.

## Relationship to eval

Automated **`forge-eval-gate`** proves behavior you encoded in YAML. This checklist catches **classes of issues** eval scenarios often omit (authz matrix, logging of PII, abuse limits). Both can run; neither replaces the other.
