---
name: lincheck
description: "Designs, runs, interprets, and troubleshoots Lincheck concurrency tests on the JVM. Use when exploring thread interleavings, testing arbitrary concurrent code, declaring concurrent data-structure operations, checking linearizability or other sequential specifications, comparing model checking with stress testing, validating obstruction freedom, or reproducing deadlocks and races. Don't use for performance benchmarking, non-JVM execution, distributed consistency, production race detection without a Lincheck model, or formal proof beyond configured executions."
compatibility: "Current Lincheck 3.7 uses coordinates org.jetbrains.lincheck:lincheck and packages org.jetbrains.lincheck. Lincheck executes only on JVM; Kotlin Multiplatform projects place Lincheck tests in JVM/Android host-test source sets. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/lincheck-guide.html"
  sourceVersion: "Lincheck 3.7 (JetBrains/lincheck@a1e02bfda2948c02605ef7ac83c433c71c67ec6c); Kotlin Help build 1155"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T15:18:42+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T15:18:42+02:00"
---

# Lincheck

## Step 1: Define the concurrency property

1. DEFINE arbitrary-code interleaving | concurrent data structure | deadlock/stall | linearizability | serializability | quiescent consistency | obstruction freedom | migration.
2. IDENTIFY shared state, operations, threads/coroutines, initialization/post phase, expected sequential behavior, blocking operations, progress guarantee, JVM test source set, and current Lincheck API/version.
3. READ the current [Lincheck guide](https://kotlinlang.org/docs/lincheck-guide.html), relevant topic page, and [latest release](https://github.com/JetBrains/lincheck/releases/latest) before API/version changes.
4. STATE the property and bounded exploration configuration. Lincheck finds counterexamples within configured executions; a passing run is not a formal proof.
5. ROUTE coroutine lifecycle/Flow design to `kotlin-coroutines` and performance measurement to `kotlinx-benchmark`.

Completion: shared state, operation boundaries, oracle/property, strategy, bounds, and platform are explicit.

## Step 2: Inspect project and tests

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM current/legacy coordinates/imports, Lincheck version/test scope, JVM test source set, arbitrary/declarative entry points, operations/parameters/validation, strategies/verifier/specification, scenario bounds, suspension/blocking flags, and progress checks. Treat source findings as candidates; inspect enclosing test classes before claims.

Completion: dependency, API generation, test source set, and every Lincheck entry point are identified.

## Step 3: Choose the testing API

- arbitrary threads/code/deadlock -> READ `references/arbitrary-code.md`.
- operation-generated data-structure scenarios -> READ `references/data-structures.md`.
- model checking versus stress and bounds -> READ `references/strategies.md`.
- verifier, sequential specification, final-state validation, progress -> READ `references/verification-progress.md`.
- JVM/KMP placement, traces, debugger, migration -> READ `references/setup-migration-debugging.md`.

USE `Lincheck.runConcurrentTest` when the test must spell out one concurrent program/assertion. USE declarative `@Operation` plus options when Lincheck should generate operation scenarios and verify against a sequential model.

Completion: API style matches whether execution steps or operation semantics are the test input.

## Step 4: Build a minimal red test

1. PLACE Lincheck only in JVM/JVM-host test scope.
2. MINIMIZE shared state and operations while preserving the suspected race/deadlock.
3. REMOVE sleeps, logging, network, wall-clock, and unrelated frameworks that distort schedules.
4. RUN model checking first when supported to obtain a deterministic trace.
5. REQUIRE the unfixed implementation to fail and capture the minimized scenario/interleaving.

Completion: a bounded test deterministically exposes the reported concurrency violation or documents why only stress can reproduce it.

## Step 5: Model arbitrary concurrent code

1. WRAP the exact concurrent program in `Lincheck.runConcurrentTest`.
2. CREATE/join all participating JVM threads inside the block and assert the required postcondition.
3. KEEP each invocation isolated; reset mutable/global state before the block.
4. SET invocation count only high enough to reproduce within acceptable test time; preserve the smallest reliable counterexample.
5. For deadlocks, retain the lock/order conditions rather than replacing joins with time sleeps.

Completion: failure trace maps directly to a violated assertion, exception, or stalled execution in the program.

## Step 6: Model a concurrent data structure

1. DECLARE every public concurrent action as an `@Operation` with observable return/exception semantics.
2. CONSTRAIN arguments to collision-heavy, boundary-rich values; wide random domains can hide races.
3. PROVIDE a simpler sequential specification when the concurrent structure's own sequential behavior is not an adequate oracle.
4. ADD `@Validate` for final-state invariants not observable from operation results.
5. MARK nonparallel/run-once/blocking/cancellable operation semantics only when they are true of the production contract.

Completion: generated scenarios cover meaningful conflicts and the oracle accepts exactly valid histories.

## Step 7: Configure strategies and bounds

1. MODEL CHECK for reproducible schedules/traces under sequential-consistency assumptions.
2. STRESS TEST for real JVM scheduling/memory-model effects not simulated by model checking.
3. START with defaults; tune threads, actors, iterations, invocations, custom scenarios, timeout, loop, and recursion bounds from the bug shape.
4. KEEP failed-scenario minimization enabled for diagnosis; disable temporarily only to inspect hidden context.
5. RUN both strategies for load-bearing algorithms when their different coverage matters.

Completion: each option increases relevant exploration rather than merely test duration.

## Step 8: Verify results and progress

1. KEEP linearizability default unless the documented contract intentionally permits weaker ordering.
2. USE serializability or quiescent consistency only with an explicit rationale and matching sequential specification.
3. VALIDATE final state separately with argument-free `@Validate` functions.
4. ENABLE obstruction-freedom checking only for a claimed nonblocking algorithm; mark truly blocking operations `blocking=true`.
5. Remember Lincheck verifies obstruction freedom only; failures disprove stronger lock/wait freedom, passes do not prove them.

Completion: verifier and progress model match the advertised data-structure contract.

## Step 9: Fix and preserve the counterexample

1. TRACE the minimized switch/read/write/lock path to the first invalid state transition.
2. FIX synchronization/atomic protocol in production code, not test bounds or instrumentation exclusions.
3. RE-RUN the exact red scenario, model checking, stress test, and ordinary functional tests.
4. KEEP a compact custom scenario when random generation might stop reaching the regression.
5. REVIEW guarantees/ignored library methods because overbroad atomic/ignore assumptions can erase switch points.

Completion: the original trace is impossible under the corrected protocol and broad scenarios still pass.

## Step 10: Verify and report

1. RUN targeted Lincheck tests repeatedly, then owning JVM test task and CI-equivalent suite.
2. CONFIRM no non-JVM task attempts to execute Lincheck in KMP.
3. INSPECT pass/fail trace, scenario, verifier, bounds, JVM/toolchain, and duration.
4. COPY `assets/lincheck-report.md`; fill property, subject/oracle, API style, strategy/options, red trace, fix, green proof, limitations, and unmodeled memory/platform behavior.

## Error Handling

- Imports/artifact unresolved -> migrate v2 `org.jetbrains.kotlinx.lincheck` coordinates/packages to v3 `org.jetbrains.lincheck` consistently.
- Test passes before fix -> narrow values, add custom scenario, expose operation results/final invariant, increase relevant bounds, or use the complementary strategy.
- Model checking misses memory-order bug -> run stress; model checking assumes sequential consistency.
- False stalled execution -> inspect real blocking/spin/recursion, then adjust `blocking`, timeout, loop, or recursion bounds narrowly.
- Suspend operation stalls forever -> model cancellation semantics with `cancellableOnSuspension` and prompt cancellation only when production promises them.
- Trace disappears after adding logging -> remove timing/instrumentation disturbance and reproduce with Lincheck trace/debugger.
- JVM reports dynamic-agent or field-offset instrumentation warnings -> verify Lincheck/JDK compatibility and whether relevant code lacked switch-point instrumentation before trusting coverage.
- KMP non-JVM task fails -> move Lincheck dependency/tests to `jvmTest` or Android host-test source set; Lincheck is JVM-only.
