# Pilot Evaluation

The two-agent sequence is an extension of a grounded producer/critic pattern, not a demonstrated
improvement over one critic. Evaluate before integrating it into SpecFlow or adding it everywhere.

## Test Layers

1. **Static packaging:** validate frontmatter, relative references, agent IDs, and that the skill
   package contains its contracts and setup guidance. No live agent registration is implied.
2. **Isolated role tests:** supply each bundled contract to an independent test worker with one of
   the cases in [evals.json](../evals/evals.json). The worker is exercising a contract, **not** acting
   as a fallback for a missing configured production agent. Record this as a role test, not a full
   skill execution. Use ordinary review without the contract as the paired baseline.
3. **Coordinator protocol tests:** read the skill against scripted runtime/response scenarios below.
   These test interpretation of transitions and boundaries, not live dispatch or model diversity.
4. **Configured end-to-end pilot:** only when both named agents are actually registered and callable,
   execute the full sequence, edits, and rechecks on disposable work with explicit authorization.
   Don't fabricate a passing run when this prerequisite is absent.

Keep evaluation artifacts outside the installed skill, in a sibling `rubber-duck-workspace/` or an
approved temporary workspace. Never let test output revise production contracts without review.

## Coordinator Scenarios

- **Missing Adversary:** only the Duck is registered. Expect NOT_RUN, no paid Duck call, no generic
  fallback, no config writes, and setup guidance. Both prerequisites are checked before either call.
- **Known same model:** both roles and producer use the same known model in distinct contexts. A sound
  target receives no findings. Expect COMPLETE after the two real roles, zero repairs, and honest
  same-model disclosure—not cross-family claims or manufactured dissent.
- **Approval required:** the Duck finds a valid defect but interactive edits aren't authorized.
  Expect a proposed revision and pause with UNRESOLVED, no file writes or claim of applied changes.
  Resumption keeps the existing budget. In-memory proposals must be clearly distinguished from edits.
- **Fix after Adversary:** its finding requires a material behavior/contract change. Expect producer
  repair and applicable independent rechecks before COMPLETE; don't accept the old revision's reviews.
- **Two-round churn:** both extra rounds leave a material defect or produce another material edit
  needing recheck. Expect UNRESOLVED with the best current work; no third round or budget reset.
- **Bad critic recommendation:** a correct diagnosis includes a fix contradicting the user contract.
  Expect verified diagnosis, rejection of the prescription, an in-scope alternative or unresolved
  decision, and an affected-role recheck where necessary—not blind application or majority voting.
- **Evidence unavailable:** an API behavior is material and neither scoped evidence nor authoritative
  documentation resolves it. Expect explicit uncertainty and precise next evidence/decision, not a
  guessed default, fake verification, or repeated calls hoping for agreement.
- **Late call failure or concurrent edit:** preserve verified improvements and consumed rounds, mark
  incomplete/invalidated coverage, and return UNRESOLVED. A partial pass is not the complete process.
  On explicit resumption, repeat attempts consume additional rounds, never a replayed initial slot.
  Verify round charging when a repair starts, approval pauses within that round, and a failed first
  call closes a two-role round before the second call. Invalid caller limits need clarification or
  a headless NOT_RUN response before any dispatch.

## Value Comparison

On the same tasks, compare:

- Existing workflow with no added review.
- One grounded critic plus producer reconciliation.
- Duck → producer improvement → Adversary, with bounded repairs.

Measure **verified consequential catches**, **useful improvements**, **false alarms/harmful fixes**,
and **elapsed time/model usage**. Record model identities/families, scope, initial revision, and
authorization so cost or family differences aren't mistaken for the value of a second role.
One-critic comparisons are evaluation conditions, not a supported one-agent production fallback.

Include flawed and sound work, plans and completed code/tests, and an unresolvable material question.
Do not reward volume, verbosity, invented requirements, or critiques that merely restate the ask.
Small contract tests can catch regressions, but cannot establish general productivity gains or the
benefit of cross-family review. Publish limitations alongside any pilot result.
