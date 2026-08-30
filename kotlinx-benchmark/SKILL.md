---
name: kotlinx-benchmark
description: "Configures, runs, compares, and troubleshoots kotlinx-benchmark for Kotlin/JVM, Java, JavaScript, Native, and Wasm projects. Use when adding the benchmark plugin and runtime, defining benchmark source sets, targets or profiles, choosing warmups, iterations, modes, forks or report formats, building JMH benchmark JARs, analyzing JSON results, or diagnosing missing benchmarks and toolchain failures. Don't use for production profiling, AndroidX Benchmark or Macrobenchmark, Java JMH without kotlinx-benchmark, load testing, or performance claims without controlled measurements."
compatibility: "kotlinx-benchmark 0.4.19 requires Kotlin 2.2.0+ and Gradle 8.0+; its experimental Wasm targets require the exact Kotlin version used to build the release (2.2.0 for 0.4.19). Native benchmarks run only for the host target. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://github.com/Kotlin/kotlinx-benchmark"
  sourceVersion: "kotlinx-benchmark 0.4.19@73284a133f1c3546668764a48d4b57663786d04b"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T14:34:58+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T14:34:58+02:00"
---

# kotlinx-benchmark

## Step 1: Define the measurement

1. DEFINE setup | benchmark implementation | target/profile change | comparison | regression investigation | failure diagnosis.
2. STATE one performance question, operation boundary, input distribution, mode, unit, baseline/candidate, and practical effect size before writing code.
3. IDENTIFY Kotlin/Gradle versions, project kind, benchmark source set/compilation, registered targets, runtime/plugin/JMH versions, host/runtime, report consumer, and existing benchmark conventions.
4. READ the current [repository guide](https://github.com/Kotlin/kotlinx-benchmark), [latest release](https://github.com/Kotlin/kotlinx-benchmark/releases/latest), and target-specific reference before version changes. Keep plugin and runtime versions identical.
5. TREAT the toolkit as Alpha and Wasm as experimental. A benchmark measures a controlled scenario; it does not explain production latency by itself.

Completion: hypothesis, metric, workload, target, toolchain, comparison method, and acceptance rule are explicit.

## Step 2: Inspect the project

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM plugin/runtime versions, Kotlin/Gradle versions, source sets/compilations, registered benchmark targets, configuration profiles, generated task names, JMH/all-open setup, report formats, and platform-specific advanced options. Resolve version-catalog and convention-plugin indirection before editing.

Completion: inspector output and Gradle task list identify every benchmark target/profile pair.

## Step 3: Configure source sets and targets

- JVM/Java or KMP target setup -> READ `references/setup-targets.md`.
- benchmark annotations/state/Blackhole -> READ `references/writing-benchmarks.md`.
- profiles/tasks/reports/JMH JAR -> READ `references/profiles-tasks.md`.
- comparison or regression claim -> READ `references/measurement-analysis.md`.
- missing benchmark/tool/runtime failure -> READ `references/troubleshooting.md`.

REUSE the repository's version catalog, source-set layout, convention plugin, wrapper, and toolchain. Add the runtime only to benchmark code's compilation/source set; do not expose it as a production API dependency.

Completion: every registered target maps to an existing Kotlin compilation/source set and compatible execution host.

## Step 4: Implement a trustworthy benchmark

1. VERIFY workload correctness with ordinary tests before timing it.
2. ISOLATE setup/teardown from the measured method unless their cost is the subject.
3. RETURN a single result or consume multiple results with `Blackhole` so optimization cannot erase work.
4. PARAMETERIZE representative inputs through public mutable primitive/String `@Param` state; avoid per-invocation randomness unless measured intentionally.
5. SELECT state scope and lifecycle level deliberately. Non-JVM targets support `Scope.Benchmark`; JVM supports JMH scopes/levels.
6. KEEP benchmark methods public and argument-free except one `Blackhole`; configure JVM Kotlin classes/methods open through all-open or explicit `open`.

Completion: the benchmark computes a verified result, retains its work, and times only the stated operation.

## Step 5: Create smoke and measurement profiles

1. KEEP a short `smoke` profile for discovery/execution validation.
2. CONFIGURE measurement warmups, iterations, iteration time, mode, output unit, parameters, includes/excludes, forks, and report format from the hypothesis.
3. REMEMBER build-script profile values override annotations.
4. USE include/exclude regular expressions against fully qualified benchmark names; list matched benchmarks before a long run.
5. USE JSON for machine comparison unless an existing consumer requires CSV/SCSV/text.

Completion: smoke finishes quickly and measurement profile has enough independent samples/forks for the chosen runtime.

## Step 6: Validate execution before measurement

1. RUN the most specific smoke task: `<target><Profile>Benchmark`.
2. REQUIRE the expected benchmark count, parameter combinations, mode, units, target, and nonzero workload result/side effect.
3. RUN the aggregate smoke task only after each target-specific task works.
4. VERIFY report file existence and parse its schema; preserve raw output and command metadata.
5. For JVM, optionally build `<target>BenchmarkJar` and run `java -jar ... -h` before profiler use.

Completion: discovery, execution, and report generation work for every intended target without claiming performance.

## Step 7: Run controlled measurements

1. BUILD benchmark binaries before the timed session; use optimized/release output where the target runner does.
2. STABILIZE machine, power mode, CPU allocation, thermal state, runtime/toolchain, background load, and process affinity according to repository policy.
3. RUN baseline and candidate in randomized/interleaved order when practical; use the same host and invocation profile.
4. COLLECT multiple forks/runs rather than one aggregate number. Never compare debug/native release, different JDKs, browsers, Node versions, or hosts as code-only effects.
5. RECORD all environment and commit identifiers with raw reports.

Completion: baseline and candidate samples differ only by the intended variable or disclose every confounder.

## Step 8: Analyze results

1. VALIDATE units, mode, sample count, errors, and parameter identity before comparing scores.
2. COMPARE like-for-like benchmark/target/profile entries; retain distribution/error information instead of only the mean.
3. CALCULATE absolute and relative change with uncertainty appropriate to repeated runs.
4. REPEAT suspicious wins/regressions, reverse run order, and inspect generated code/profiler evidence before assigning cause.
5. REPORT practical effect size and limitations. Avoid hard CI regression gates on heterogeneous runners; use controlled dedicated hardware and noise-aware thresholds when gating is required.

Completion: every claim is supported by comparable raw observations and names uncertainty/confounders.

## Step 9: Integrate maintenance workflow

1. RUN smoke benchmarks for benchmark-source changes where CI cost permits.
2. RUN full measurements on scheduled/manual dedicated workers, not every shared CI build by default.
3. VERSION raw reports outside transient build output when they are comparison baselines.
4. REVIEW benchmark changes like tests: input, timed boundary, state, optimizer defenses, target coverage, and result schema.
5. UPDATE plugin/runtime/JMH/Kotlin versions through a baseline-reset experiment; never merge toolchain drift into a code-regression claim.

Completion: CI validates benchmark executability and controlled infrastructure owns performance claims.

## Step 10: Report completion

COPY `assets/benchmark-report.md`; fill exact hypothesis, code boundary, versions, target/profile, environment, raw report paths, sample/result table, comparison, uncertainty, profiler evidence, conclusion, and limitations.

## Error Handling

- No benchmark discovered -> verify runtime dependency, source set/compilation association, target registration, public `@Benchmark`, include regex, and task name.
- JVM generation fails on final class/method -> apply all-open for `org.openjdk.jmh.annotations.State` or mark benchmark types/methods open.
- Plugin/runtime linkage fails -> align both to one version and verify Kotlin/Gradle compatibility; 0.4.18 had recent-Kotlin breakage reverted in 0.4.19.
- Native task absent/fails -> run only the host target and verify target registration/build type.
- JS/Wasm task fails -> verify Node environment, executor, bridge option, and exact Wasm Kotlin version.
- Result is implausibly fast/zero -> return/consume outputs, inspect constant folding/dead-code elimination, enlarge representative state, and use profiler/generated-code evidence.
- Results fluctuate -> increase forks/iterations, isolate the host, inspect GC/thermal/frequency effects, and report inconclusive evidence rather than averaging away noise.
