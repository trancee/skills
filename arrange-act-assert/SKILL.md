---
name: arrange-act-assert
description: "Structures, reviews, and refactors automated tests with Arrange-Act-Assert. Use when writing unit, integration, API, UI, or end-to-end tests; separating setup from the behavior under test and observable outcomes; diagnosing tests with multiple actions, hidden assertions, oversized setup, or unclear failures; translating Given-When-Then; or standardizing test readability across languages. Don't use for choosing test strategy or coverage, the TDD workflow itself, property- or model-based tests whose natural structure differs, benchmarks, production code organization, or mechanically adding AAA comments to already-clear tests."
compatibility: "Framework- and language-agnostic. Inspector recognizes common Python, Kotlin, Java, JavaScript/TypeScript, C#, Go, Ruby, Rust, and Swift test forms using deterministic heuristics; review reported candidates in context. Requires Python 3.11+."
metadata:
  category: "development"
  source: "https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/"
  sourceVersion: "Automation Panda 2020-07-07; Semaphore updated 2025-01-17; supplied Medium articles 2017-09-09 and 2023-05-09"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T12:36:26+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T12:36:26+02:00"
---

# Arrange Act Assert

## Step 1: Define one observable behavior

1. IDENTIFY the public seam, precondition, one focal behavior, and observable outcome before editing the test.
2. NAME the test as behavior + condition + expected result in repository vocabulary; avoid names that restate a method or say only “works.”
3. CONFIRM the test layer and real contract are already chosen. ROUTE test-first red/green sequencing to `tdd`, seam/module design to `codebase-design`, and framework-specific setup to its development skill.
4. USE Arrange-Act-Assert for an example-based scenario with a focal action. If the test is naturally property-based, model-based/state-machine, benchmark, fuzz, approval/snapshot, or long Given-When-Then workflow, preserve that framework’s clearer native structure.
5. READ `references/phase-rules.md` before deciding whether a call belongs to Arrange, Act, or Assert.

Completion: a reader can state “Given [precondition], when [behavior], then [outcome]” without reading implementation details.

## Step 2: Inspect candidate tests

RUN from the repository root:
```bash
python3 scripts/inspect-tests.py --root . --json
```

NARROW with `--path tests/path` and framework suffixes as needed. The inspector reports assertion-less, skipped, sleeping, oversized, and malformed explicit AAA-marker candidates; it never requires phase comments.

REVIEW every finding against repository conventions and the public behavior. Heuristics identify candidates, not proof.

Completion: each changed test’s focal behavior, phase boundaries, assertions, and cleanup are accounted for.

## Step 3: Establish the three-phase shape

1. WRITE phases in strict order: Arrange, Act, Assert. Separate them with blank lines when that improves scanning.
2. USE `// Arrange`/`# Arrange` comments only when teaching, repository convention, or complex setup makes boundaries genuinely ambiguous. Remove comments that merely narrate obvious whitespace.
3. KEEP the Act visually easy to find and the Assert cluster adjacent to it. Move cleanup to guaranteed teardown/finally mechanisms rather than interleaving it with assertions.
4. TRANSLATE Given -> Arrange, When -> Act, Then -> Assert when moving between BDD and code-level tests; preserve domain wording.
5. FOR parameterized/table tests, run one complete AAA scenario per case rather than sharing mutable Act/Assert state across cases.

Completion: phase order is visible without relying on comments, and no later phase mutates an earlier phase’s responsibility.

## Step 4: Arrange only what the scenario needs

1. CREATE inputs, dependencies, fakes, clock/randomness, fixtures, database/server state, and system state required for this behavior—nothing speculative.
2. PUT expected values beside their independent source of truth. Do not calculate expected output with the same algorithm as the system under test.
3. CONFIGURE stubs/fakes in Arrange; reserve interaction verification for Assert. Prefer stateful fakes or real lightweight dependencies over mocks of implementation details.
4. USE builders/factories for valid defaults while overriding only scenario-relevant fields. Keep important test values visible in the test body.
5. MOVE repeated mechanical setup to helpers/fixtures only when the helper’s name and return value preserve the scenario. Avoid assertions or hidden focal actions inside Arrange helpers.
6. FAIL fixture construction as setup error/precondition where the framework distinguishes it; do not let broken Arrange masquerade as product assertion failure.

Completion: removing any Arrange line either breaks the stated precondition or makes the expected outcome unreadable.

## Step 5: Act on one focal behavior

1. PERFORM one logical behavior at the public seam. Prefer one invocation, request, user gesture, message, or transition.
2. CAPTURE the result, exception, emitted event, response, or new observable state needed by Assert; do not assert while producing it unless the framework idiom necessarily combines Act and Assert.
3. AWAIT asynchronous completion using deterministic clocks/idleness/signals. Fixed sleeps are not part of Act.
4. IF a realistic behavior inherently requires several low-level calls, wrap them in one domain action or keep the short sequence together and name the workflow. If it tests distinct behaviors, split tests.
5. DO NOT add another Act after assertions to extend a scenario. Create a separate test or use explicit Given-When-Then/state-machine form when history itself is the contract.

Completion: changing/removing the Act prevents the asserted outcome, while Arrange alone cannot produce it.

## Step 6: Assert one coherent outcome cluster

1. ASSERT public outputs, visible state, emitted events, persisted behavior, protocol response, or required collaborator interaction caused by Act.
2. USE one or several related assertions when they describe one outcome. Do not split an atomic contract merely to satisfy “one assertion,” and do not combine unrelated outcomes in one test.
3. COMPARE expected before actual according to framework convention and include diagnostics only when the assertion library cannot explain the mismatch.
4. VERIFY exceptions by type and relevant stable fields/message fragments. A helper such as `assertThrows`/`assertFailsWith` may combine Act and capture; keep follow-up assertions on the exception in Assert.
5. VERIFY mock interactions only when the interaction is itself the public boundary. Prefer observable result/state otherwise; avoid `verifyNoMoreInteractions` that freezes irrelevant implementation.
6. ASSERT eventual outcomes with bounded polling/idleness using meaningful failure output; never convert a race into a larger sleep.

Completion: every assertion can fail under a plausible defect in the focal behavior, and no assertion tests incidental implementation.

## Step 7: Handle integration, UI, async, and side effects

READ `references/async-integration.md`.

1. ARRANGE isolated resources/transactions/servers/users and deterministic time/IDs; make ownership unique for parallel suites.
2. ACT through the same public transport/UI/API used by consumers; avoid setup backdoors in Act.
3. ASSERT through the contract’s observable boundary. Use a direct database query only when persistence itself is the boundary, not as a hidden implementation side channel.
4. FOR UI, treat one user intent as Act and assert accessible semantics/navigation/state; use framework idleness and clocks.
5. FOR events/jobs, subscribe or establish observers in Arrange, trigger in Act, and await/assert bounded results in Assert.
6. REGISTER cleanup before Act and guarantee it in fixture teardown/finally even when Act or Assert fails.

Completion: isolation, synchronization, observation, and cleanup remain correct under failure and parallel execution.

## Step 8: Keep test helpers phase-specific

1. NAME helpers by phase responsibility: `givenValidCart`, `submitOrder`, `assertOrderAccepted`, or repository equivalents.
2. KEEP Arrange helpers deterministic and mutation-limited to declared fixtures; return handles needed for cleanup/observation.
3. KEEP Act helpers focused on one public behavior and expose its outcome instead of swallowing errors or asserting internally.
4. KEEP assertion helpers domain-specific, side-effect free, and rich in mismatch diagnostics.
5. AVOID a single “test scenario” helper that arranges, acts, and asserts invisibly; it makes passing tests unreadable and failures hard to localize.

Completion: opening a helper reveals one phase only, and the test body still states the behavior.

## Step 9: Refactor existing tests safely

READ `references/refactoring.md`.

1. RECORD current test intent, public seam, and whether it fails/passes before structural edits.
2. LOCATE setup, focal behavior, observations, assertions, cleanup, and unrelated secondary acts.
3. MOVE code into AAA order without changing inputs/timing/assertion semantics first.
4. SPLIT repeated Act-Assert cycles only when each test can independently arrange the required precondition without losing a workflow/history contract.
5. EXTRACT noisy setup/assertion helpers after the phases are clear; delete dead setup and implementation-coupled verification.
6. RUN each changed test after every semantic split, then its owning suite. Verify the test still fails under a plausible mutation/known bug.

Completion: refactoring preserves or deliberately sharpens the observable contract, and each resulting test can fail for its named behavior.

## Step 10: Review and report

READ `references/review-checklist.md`.

1. VERIFY phase order, one focal Act, coherent assertions, deterministic synchronization, isolation, cleanup, naming, and public-seam focus.
2. RUN the narrow changed tests and owning suite with repository commands; no source-format audit substitutes for behavior execution.
3. COPY `assets/aaa-review.md`; record behavior/seam, phase mapping, smells/refactors, verification, and justified exceptions.

Completion: every checklist item passes or the report names why another structure is clearer.

## Error Handling

- Arrange contains assertions -> move outcome verification to Assert; retain only explicit fixture precondition failures where the framework distinguishes setup errors.
- Act contains setup -> move prerequisite creation/configuration earlier; keep only the behavior trigger and result capture.
- Test has Act-Assert-Act-Assert -> split independent behaviors or adopt an explicit workflow/state-machine scenario.
- Assertion-less test -> add a contract assertion or delete/rename it as a smoke harness that reports failures through a documented oracle.
- Setup dominates the test -> extract a named fixture/builder while keeping scenario-critical values visible.
- Mock verification breaks on refactor -> assert public output/state or verify only the boundary interaction that is the contract.
- Phase comments add noise -> remove them and use whitespace/names; comments are teaching/ambiguity aids, not required syntax.
- Async test sleeps -> use virtual time, idleness, signals, or bounded eventual assertions.
- AAA feels forced -> preserve the natural property/model/BDD/benchmark structure and document the exception.
