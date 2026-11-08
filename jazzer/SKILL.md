---
name: jazzer
description: "Installs, integrates, runs, and troubleshoots Jazzer coverage-guided JVM fuzzing. Use for JUnit fuzz tests, standalone Java/Kotlin JVM fuzz targets, structured input mutation, corpus and crash management, sanitizer findings, and JNI fuzzing. Don't use for Jazzer.js, non-JVM fuzzers, Android device instrumentation, or claims that a bounded fuzz run proves security."
compatibility: "Requires a compatible full JDK and Jazzer native runtime: upstream supports Linux x86_64/arm64, macOS 12+ x86_64/arm64, Windows x86_64. JUnit integration requires Jupiter 5.9+. Smoke baseline: Jazzer 0.30.0, JDK 21. Corpus inventory: Python 3.10+, stdlib only."
metadata:
  category: "testing-quality"
  source: "https://github.com/CodeIntelligenceTesting/jazzer"
  sourceVersion: "v0.30.0 @ dd9416b74d263b56fc848cd782b061baf5f962a6; docs accessed 2026-11-08"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-11-08T14:19:29+01:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-11-08T14:19:29+01:00"
---

# Jazzer

PATHS: resolve resources from this activated package, not the target repository. This independently authored skill does not install Jazzer or bundle native runtime JARs. Pin the tool/dependencies and preserve the selected JDK, target signature and corpus provenance.

## Step 1: Select the boundary and execution route

1. RECORD the application entry point, invariant/security property, target classes/methods, existing test/build conventions, OS/architecture, full JDK and Jazzer version. Distinguish a regression replay from a new coverage-guided campaign.
2. JUnit-capable JVM project -> READ [references/junit.md](references/junit.md) and integrate a pinned test-scoped `jazzer-junit` dependency. Standalone target/replay -> READ [references/standalone.md](references/standalone.md). Prefer existing JVM test infrastructure; do not move runtime fuzz dependencies into production.
3. READ [references/targets.md](references/targets.md) before defining inputs/oracles. Use raw bytes for a raw parser, `FuzzedDataProvider` for explicit consumption, or supported typed parameters for structured values. Keep expected rejection separate from assertions and unexpected failures.
4. Hook/detector, JNI sanitizer, configuration or upstream build work -> READ [references/advanced.md](references/advanced.md). Fuzzing hooks are not a sandbox; isolate filesystem/network/process effects, remove live secrets, and obtain authorization before dangerous/elevated tests or external disclosure.

DONE: the requested behavior is reached by a supported target with a meaningful oracle, bounded isolated workload, explicit tool/JDK pin and selected execution mode.

## Step 2: Integrate and prove the target executes

1. For a disposable JUnit probe, copy [assets/pom.xml](assets/pom.xml) and [assets/SortFuzzTest.java](assets/SortFuzzTest.java) using the directory layout in `references/junit.md`. For a standalone parser probe, copy [assets/Base64Target.java](assets/Base64Target.java) and use the compile/run recipe in `references/standalone.md`.
2. Adapt the target to actual application code, supported input types and state reset. JUnit's default `PER_TEST` lifecycle does not reset before each mutation; use deliberate reset or supported `PER_EXECUTION` where needed. Unsupported mutator types/null domains are design decisions, not reasons to blanket-ignore exceptions.
3. Create target-specific seed/corpus/finding destinations before running. Use real representative and edge inputs; typed corpus bytes require Jazzer serialization, not hand-authored text guessed from parameter names. Preserve binary files unchanged across source control and upgrades.
4. Run regression first. Then enable `JAZZER_FUZZ=1` for exactly one selected JUnit fuzz method, or invoke the standalone launcher with one target and explicit libFuzzer limits. Check test discovery, instrumentation logs, actual mutating executions and termination; skipped/cached/regression-only runs are not fuzz proof.

DONE: the selected target's instrumented code executes under mutation, accepted/rejected input paths and meaningful assertions work, and corpus/artifact output locations are known.

## Step 3: Run and diagnose a bounded campaign

1. Set duration/execution/input/resource bounds appropriate to the application and keep target/thread/global state deterministic. Persist the exact command, working directory, JDK/build/classpath, Jazzer config and initial seeds.
2. Inspect coverage/features and target paths, not only execution count or corpus size. Tighten instrumentation to relevant implementation packages when dependency exploration dominates, but retain the code required to test the invariant.
3. Use value profiling/dictionaries/typed value pools only for a justified input gate. Preserve API-valid and malformed domains rather than filtering away defects. Distinguish Jazzer double-dash options from libFuzzer single-dash options and JVM arguments.
4. On a finding, preserve stack/dedup token/raw artifact and generated reproducer. Stop or snapshot the corpus, then RUN `python3 <skill-directory>/scripts/inventory-corpus.py <corpus-or-crash-path>` to record stable file paths, sizes and SHA-256. The read-only CLI requires Python 3.10+, emits JSON, and exits 2 on unreadable/unsupported/symlink inputs; it does not infer coverage, decode structured inputs or delete duplicates.
5. Timeouts/OOMs, sanitizer hooks, uncaught exceptions and failed oracles require separate triage. Do not disable hooks, ignore tokens or broaden catch clauses to make the campaign green. More executions or no finding in a budget does not establish security.

DONE: the campaign's actual executed targets, budget/termination, coverage boundary and any findings are captured without hiding rejected signals.

## Step 4: Replay, fix and deliver

1. Replay the original artifact as the only positional file input with the same target/config. If a Java reproducer exists, inspect/run it with matching dependencies; detector-only findings may still require instrumented replay. Verify the same defect, not merely a nonzero exit.
2. Minimize into a separate artifact while retaining the original. Fix the root cause in the real implementation, replay original/minimized inputs, and retain a deterministic consumer-visible regression in the project's established tests/resources where the seam is correct.
3. Run a fresh bounded campaign on the final target and fix. Verify relevant code was instrumented and state reset remains sound; a plain JUnit regression pass alone is not proof of new fuzzing. JNI/native paths require their own instrumented report, not the Java probes.
4. COPY [assets/findings.md](assets/findings.md) or use its fields in a short report. State observation versus vulnerability/causal interpretation, input provenance, replay/fix evidence, coverage and unexercised platforms/integrations. Do not upload crashes or propose public disclosure without authorization.
5. Stop owned fuzz workers/query/debug sessions and remove disposable downloads/builds/probe outputs. Preserve user corpora and requested findings; do not commit generated runtime artifacts or unrelated changes.

## Error Handling

- Native launcher cannot find libjvm -> check full JDK JAVA_HOME and OS/architecture; inspect launcher diagnostics before reinstalling.
- Class/bytecode instrumentation failure -> match runtime/compiler/dependency versions and target classpath; keep instrumentation enabled rather than suppressing it.
- JUnit reports no fuzzing -> inspect selected method, environment forwarding, Jupiter discovery and Gradle caching; one JVM fuzzes one selected method.
- No structured mutator or ignored seed -> choose supported types/serialization and confirm startup seed execution; do not count warnings/skips as coverage.
- Crash not in expected resources -> inspect actual working-directory fallback and output logs; preserve binary artifacts before migrating them.
- Replay is flaky -> capture/reset state or encode the necessary operation sequence; changing random seed alone is not a fix.
- Detector fires on legitimate test infrastructure -> establish narrowly scoped, authorized resources with the release API; retain the security property and instrumented verification.
