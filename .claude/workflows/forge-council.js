export const meta = {
  name: 'forge-council',
  description: 'Forge council span as a dynamic workflow: over a locked PRD, fan out the 4 surface reasonings (backend/web/app/infra) and 5 contract analyses (REST/events/cache/DB/search) in parallel, adversarially cross-check them for inconsistencies, and synthesize a DRAFT shared-dev-spec written to the brain for human review. Does NOT freeze the spec — spec-freeze remains a human gate.',
  phases: [
    { title: 'Surfaces', detail: 'backend/web/app/infra reasoning in parallel' },
    { title: 'Contracts', detail: 'REST/events/cache/DB/search analysis in parallel' },
    { title: 'Cross-check', detail: 'adversarial consistency verification per contract' },
    { title: 'Synthesize', detail: 'one agent writes shared-dev-spec.DRAFT.md to the brain' },
  ],
}

// ── Inputs ────────────────────────────────────────────────────────────────
// args: { task_id: "<id>", brain?: "<brain root>" }
const taskId = (args && args.task_id) || null
const brain = (args && args.brain) || '~/forge/brain'
// Brain paths may start with ~ (the operator home). The workflow runtime has no filesystem
// access, but the subagents it spawns do — and the Read/Write tools want absolute paths. So
// every agent prompt below carries this note telling the agent to expand ~ itself.
const BRAIN_NOTE =
  'NOTE: brain paths may begin with "~" (the operator home directory). Before any Read or Write, ' +
  'expand "~" to an absolute path yourself (e.g. run `echo $HOME`) — the file tools require absolute paths.'
if (!taskId) {
  log('forge-council: pass {task_id:"<id>"}. The locked PRD must exist at prds/<task_id>/prd-locked.md in the brain.')
  return { error: 'missing task_id' }
}
const prdPath = `${brain}/prds/${taskId}/prd-locked.md`
const taskDir = `${brain}/prds/${taskId}`
log(`forge-council for task ${taskId} — reading locked PRD at ${prdPath}`)

// ── Schemas ────────────────────────────────────────────────────────────────
const SURFACE_SCHEMA = {
  type: 'object',
  properties: {
    responsibilities: { type: 'array', items: { type: 'string' } },
    owns: { type: 'array', items: { type: 'string' }, description: 'Interfaces/data this surface owns' },
    consumes: { type: 'array', items: { type: 'string' }, description: 'Interfaces/data this surface depends on from others' },
    risks: { type: 'array', items: { type: 'string' } },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['responsibilities', 'owns', 'consumes', 'risks'],
}
const CONTRACT_SCHEMA = {
  type: 'object',
  properties: {
    contract: { type: 'string' },
    producer: { type: 'string' },
    consumers: { type: 'array', items: { type: 'string' } },
    shape: { type: 'string', description: 'Proposed interface/schema/topic/keys, concretely' },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['contract', 'shape'],
}
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    contract: { type: 'string' },
    consistent: { type: 'boolean' },
    conflicts: { type: 'array', items: { type: 'string' }, description: 'Where surfaces disagree about this contract' },
  },
  required: ['contract', 'consistent'],
}

// ── Phase 1: Surfaces (parallel, gate-free) ─────────────────────────────────
phase('Surfaces')
const SURFACES = [
  { key: 'backend', skill: 'reasoning-as-backend' },
  { key: 'web', skill: 'reasoning-as-web-frontend' },
  { key: 'app', skill: 'reasoning-as-app-frontend' },
  { key: 'infra', skill: 'reasoning-as-infra' },
]
const surfaces = (await parallel(SURFACES.map((s) => () =>
  agent(
    `You are the ${s.key} surface in a Forge council. Read the locked PRD at ${prdPath} ` +
    `and follow the Forge \`${s.skill}\` skill — invoke it by name via the Skill tool (it is installed as a plugin skill, not a file in this project's working directory). ` +
    `Produce this surface's reasoning: ` +
    `responsibilities, the interfaces/data it OWNS, what it CONSUMES from other surfaces, risks, and open questions. ` +
    `Be concrete and cite specifics from the PRD. ${BRAIN_NOTE}`,
    { label: `surface:${s.key}`, phase: 'Surfaces', schema: SURFACE_SCHEMA }
  ).then((r) => ({ surface: s.key, ...r }))
))).filter(Boolean)

// ── Phase 2: Contracts (parallel) ───────────────────────────────────────────
phase('Contracts')
const CONTRACTS = [
  { key: 'api-rest', skill: 'contract-api-rest' },
  { key: 'events', skill: 'contract-event-bus' },
  { key: 'cache', skill: 'contract-cache' },
  { key: 'schema-db', skill: 'contract-schema-db' },
  { key: 'search', skill: 'contract-search' },
]
const surfacesJson = JSON.stringify(surfaces)
const contracts = (await parallel(CONTRACTS.map((c) => () =>
  agent(
    `You negotiate the ${c.key} contract for a Forge council. Read the locked PRD at ${prdPath}, ` +
    `follow the Forge \`${c.skill}\` skill (invoke it by name via the Skill tool), and reconcile against the surface reasonings: ${surfacesJson}. ` +
    `Propose the concrete contract (producer, consumers, shape) and list open questions. ` +
    `If this contract is not relevant to the PRD, say so and return an empty shape. ${BRAIN_NOTE}`,
    { label: `contract:${c.key}`, phase: 'Contracts', schema: CONTRACT_SCHEMA }
  ).then((r) => ({ key: c.key, ...r }))
))).filter(Boolean)

// ── Phase 3: Cross-check (adversarial, parallel) ────────────────────────────
phase('Cross-check')
const verdicts = (await parallel(contracts.map((c) => () =>
  agent(
    `Adversarially check the ${c.key} contract for cross-surface inconsistency. ` +
    `Contract proposal: ${JSON.stringify(c)}. Surface reasonings: ${surfacesJson}. ` +
    `Does every producer/consumer claim line up with what the surfaces said they own/consume? ` +
    `Default to consistent=false if you find any mismatch; list the conflicts.`,
    { label: `verify:${c.key}`, phase: 'Cross-check', schema: VERDICT_SCHEMA }
  )
))).filter(Boolean)
const conflicts = verdicts.filter((v) => v && v.consistent === false)
log(`cross-check: ${conflicts.length}/${verdicts.length} contracts have unresolved conflicts`)

// ── Phase 4: Synthesize → write DRAFT spec to brain ─────────────────────────
phase('Synthesize')
const summary = await agent(
  `Synthesize a Forge shared-dev-spec DRAFT for task ${taskId} from the council outputs.\n\n` +
  `Surfaces: ${surfacesJson}\n\nContracts: ${JSON.stringify(contracts)}\n\nCross-check verdicts: ${JSON.stringify(verdicts)}\n\n` +
  `Follow the Forge \`council-multi-repo-negotiate\` and \`spec-freeze\` skills (invoke them by name via the Skill tool) for the section structure. ` +
  `${BRAIN_NOTE} Write the result to ${taskDir}/shared-dev-spec.DRAFT.md (create the directory if needed; do NOT overwrite an existing shared-dev-spec.md). ` +
  `At the top, add a frontmatter block with type: spec and status: DRAFT, and a "## Unresolved conflicts" section listing every conflict from the cross-check so a human can resolve them before spec-freeze. ` +
  `Return a short summary of what you wrote and the count of unresolved conflicts.`,
  { label: 'synthesize:draft-spec', phase: 'Synthesize' }
)

return {
  task_id: taskId,
  surfaces: surfaces.map((s) => s.surface),
  contracts: contracts.map((c) => c.key),
  unresolved_conflicts: conflicts.length,
  draft: `${taskDir}/shared-dev-spec.DRAFT.md`,
  summary,
  note: 'DRAFT only — human spec-freeze gate still applies (Dynamic Workflows cannot take mid-run human approval).',
}
