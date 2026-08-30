# Measurement and comparison

## Experimental design

Define before execution:
- operation and excluded setup
- baseline/candidate commits
- target/runtime/toolchain
- parameters and input distribution
- Throughput or AverageTime
- output unit
- warmup, iteration duration/count, forks, run count
- practical regression threshold
- environment controls

Use a smoke profile only for correctness/discovery. Do not draw performance conclusions from its short run.

## Environment

Record CPU/model, core allocation/affinity, OS/kernel, governor/power mode, memory, JVM/Node/browser/native toolchain and flags, GC, plugin/Kotlin/JMH versions, commit, thermal state, and background load. Build before measurement. Run comparable optimized artifacts.

Interleave or randomize baseline/candidate order to reduce drift. Repeat across process forks and independent sessions. On JVM, warmup addresses JIT state but not thermal/OS/background noise. Native, JS, and Wasm have different optimizer/runtime effects; compare only within one platform/runtime configuration.

## Analysis

1. Parse raw JSON and group by benchmark FQN, target, profile, parameters, mode, and unit.
2. Reject missing/error/incomparable entries.
3. Retain individual fork/run observations and reported error, not only aggregate score.
4. Compute absolute delta and relative change with uncertainty/confidence appropriate to sample design.
5. Check order effects, outliers, GC, compilation, throttling, and bimodality.
6. Repeat and profile before attributing causality.

Throughput higher is better; AverageTime lower is better. Unit conversion errors can reverse/magnify claims.

## Regression gates

Shared CI runners rarely support tight stable thresholds. Prefer scheduled/manual dedicated workers, multiple baselines, noise-aware limits, and reruns. A threshold breach starts investigation; it is not proof of a code regression. Report inconclusive data explicitly.
