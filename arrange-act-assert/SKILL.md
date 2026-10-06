---
name: arrange-act-assert
description: "Structures and refactors example-based tests with Arrange-Act-Assert. Use for hidden focal actions, mixed phases, unrelated assertions, oversized setup, nondeterministic synchronization, or test-helper design. Don't use for test strategy, TDD sequencing, benchmarks, property/model tests, or mechanically adding phase comments."
compatibility: "Framework/language-agnostic. Python 3.11+ inspector uses heuristics; review candidates against the test's public contract."
metadata:
  category: "development"
  source: "https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/"
  sourceVersion: "Automation Panda 2020-07-07 (modified_time unchanged, checked 2026-10-06); Semaphore 2025-01-17; supplied Medium articles 2017-09-09 and 2023-05-09"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T12:36:26+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-06T15:15:21+02:00"
---

# Arrange Act Assert

## 1. Scope

1. DEFINE public seam, precondition, focal behavior, observable outcome, and existing test layer.
2. NAME behavior + condition + expected result using repository vocabulary.
3. ROUTE TDD sequencing to `tdd`, seam design to `codebase-design`, framework setup to its domain skill.
4. PRESERVE clearer property/model/fuzz/benchmark/snapshot or genuine workflow structure; AAA is not compulsory.
5. READ `references/phase-rules.md` for ambiguous causal roles; `references/source-notes.md` for source rationale.

Gate: “Given [precondition], when [behavior], then [outcome]” follows from the test's public contract.

## 2. Inspect

Resolve `scripts/` from the skill package; pass the target repository to `--root`:

```bash
python3 scripts/inspect-tests.py --root path/to/repository --json
```

NARROW with `--path`. REVIEW assertion-less/skipped/sleeping/oversized/AAA-marker candidates in context. Heuristics are not proof; comments are optional.

Gate: every changed test has known phases, focal action, oracle, cleanup, and current result.

## 3. Arrange

1. CREATE only required inputs, dependencies, fake behavior, clock/randomness, and resource state.
2. REGISTER observers and guaranteed teardown before Act; cleanup must survive setup/action/assertion failure.
3. DERIVE expected values independently from the contract, not the SUT's algorithm.
4. PREFER lightweight real dependencies/stateful fakes over implementation mocks. Configure stubs here; verify interactions in Assert.
5. USE builders for valid defaults; leave scenario-critical overrides visible. Helpers establish preconditions without hidden focal actions or outcome assertions.
6. REPORT broken fixture construction as setup failure, not a product assertion.

Gate: removing an Arrange line breaks a required precondition or hides the oracle.

## 4. Act

1. TRIGGER one logical behavior at the public seam; capture result/error/event/state.
2. KEEP a necessary short multi-call workflow together; split independent behaviors. Exception-capture helpers may combine Act with the initial type assertion.
3. AWAIT deterministic completion through clocks/idleness/signals; no fixed sleeps or speculative retries.
4. KEEP Act adjacent to Assert. Another Act after assertions needs an independent test or explicit workflow/state-machine structure.

Gate: Act causes the asserted outcome; Arrange alone cannot produce it.

## 5. Assert

1. VERIFY public outputs, state, events, persistence, protocol/UI response, or contractually required interaction.
2. GROUP related assertions for one coherent outcome; one assertion is not mandatory.
3. FOLLOW the framework's expected/actual order and useful mismatch diagnostics.
4. CHECK errors by type and stable fields/message fragments; follow exception capture with field assertions.
5. VERIFY mocks only when the interaction is the public boundary; avoid freezing incidental calls with `verifyNoMoreInteractions`.
6. USE bounded eventual assertions/idleness, not larger sleeps.

Gate: every assertion detects a plausible consumer-visible defect without incidental implementation coupling.

## 6. Specialize and refactor

- async/integration/UI/events -> READ `references/async-integration.md`; isolated resources, deterministic synchronization, pre-registered observers, guaranteed cleanup.
- existing test restructure -> READ `references/refactoring.md`; preserve inputs/timing/oracle first, then split independent behaviors.
- examples needed -> READ `references/examples.md`.

1. ORDER Arrange -> Act -> Assert; blank lines expose phases. Keep comments only for ambiguity, teaching, or repository convention.
2. TRANSLATE Given/When/Then without losing domain semantics. Each parameterized case owns its complete scenario and mutable state.
3. EXTRACT phase-specific helpers: Arrange returns owned handles; Act exposes results; Assert is side-effect-free with useful diagnostics.
4. DELETE dead setup and implementation-coupled checks. Keep workflow history when it is the contract.
5. RUN each semantic split and its owning suite; use a known defect/mutation to prove sensitivity.

Gate: phase order, causal focus, independent cases, guaranteed cleanup, and helper responsibilities remain visible.

## 7. Verify

READ `references/review-checklist.md`. RUN narrow tests and owning suite. COPY `assets/aaa-review.md`; record seam/phase mapping, refactors, commands/results, and justified native-structure exceptions.

Gate: every applicable checklist item passes or has a concrete reason for a clearer alternative.

## Failure routing

- Assertions in Arrange -> move outcome checks to Assert; retain explicit fixture preconditions only.
- Setup in Act -> establish prerequisites earlier.
- Act/Assert repeats -> split independent behavior or use explicit workflow/model steps.
- No oracle -> add a public-contract assertion or classify a smoke harness with its actual failure oracle.
- Setup dominates -> named fixture/builder; important values stay visible.
- Mock breaks on refactor -> public output/state or boundary interaction.
- Phase comments add nothing -> remove; whitespace/names carry structure.
- Sleeps/races -> virtual time, idleness, signals, or bounded eventual checks.
