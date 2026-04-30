# Forge Ethos

Five principles that govern every skill, agent, and workflow in Forge. Skills reference these rather than re-explaining them inline.

---

## 1. Iron Law over Convenience

Discipline enforced by skills — TDD, eval gates, no production code before a failing test — is non-negotiable regardless of perceived simplicity or time pressure. Every rationalization for skipping a gate ("this is just a config change", "tests can come later", "it's too simple to need eval") has caused a production incident. Skills exist to prevent those incidents, not to slow you down.

---

## 2. Brain as System of Record

Decisions, specs, eval results, and learnings live in `~/forge/brain/` committed to git. Chat is ephemeral — it disappears when the context window compacts. Brain files are the only transport layer between parallel agents, between sessions, and between humans and machines. If it isn't in the brain, it doesn't exist.

---

## 3. Gates Before Merge

Nothing ships without passing the sequence in order:

1. QA CSV approved
2. Eval YAML authored
3. TDD RED tests written
4. Implementation (GREEN)
5. Code review passed
6. Eval GREEN (all scenarios pass)

Partial pipelines are not shippable. A PR that skipped eval is not "90% done" — it is zero percent done on the gate that catches production failures. There are no half-gates.

**Not a literal CI DAG:** The numbered list above is **conceptual** (all of it must happen before merge; order can overlap in real work — e.g. semantic machine eval and TDD RED interleave in **State 4b**). The **authoritative** sequencing, log markers, and human gates are defined in **[`skills/conductor-orchestrate/SKILL.md`](skills/conductor-orchestrate/SKILL.md)** and `~/forge/brain/prds/<task-id>/conductor.log` — not by re-sorting this list in isolation.

---

## 4. Spec Before Code

Every feature starts locked in `shared-dev-spec.md`. Code is a consequence of a locked spec, not a draft of one. Writing code before the spec is locked means writing code that may need to be thrown away when the spec changes. The spec is the cheapest place to find problems.

---

## 5. Escalate, Don't Invent

When blocked — ambiguous requirements, conflicting constraints, failing gates that won't pass — write the blocker to the brain and escalate to a human. Do not invent solutions for ambiguous requirements. Do not work around failing gates. Do not resolve conflicts by guessing which stakeholder is right. The cost of an invented solution that turns out to be wrong is always higher than the cost of asking.
