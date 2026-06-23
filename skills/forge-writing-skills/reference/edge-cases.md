# forge-writing-skills — Edge Cases & Fallback Paths

## Edge Cases & Fallback Paths

### Case 1: {Descriptive scenario name}

- **Symptom:** Exact observable state
- **Do NOT:** The wrong thing (and why it's wrong)
- **Action:** Numbered steps for the correct response
```

**Rules:**
- Minimum 5 edge cases (rigid), 3 (flexible)
- Each case has symptom, "Do NOT", and action
- "Do NOT" is specific (not "don't be wrong")
- Action is numbered and concrete
- Include: infrastructure failures, upstream phase failures, policy conflicts, ambiguous inputs, resource exhaustion

---

### Step 8: Write Output Section + Checklist

**Output section:**
```markdown
Output: **{SUCCESS STATE}** ({conditions}) or **{FAILURE STATE}** ({conditions and action})
```

**Checklist (rigid skills):**
```markdown
