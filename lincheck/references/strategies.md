# Lincheck testing strategies

Sources: [Testing strategies](https://kotlinlang.org/docs/lincheck-testing-strategies.html) and [options](https://kotlinlang.org/docs/lincheck-testing-strategies-options.html).

## Model checking

Controls scheduling by instrumenting shared-memory and synchronization points. Produces reproducible detailed traces and minimizes failures. Assumes sequential consistency; misses reordering/cache effects under the relaxed Java Memory Model and may not model some standard-library behavior such as weak references.

## Stress

Runs scenarios repeatedly under OS/JVM scheduling. Faster, no sequential-consistency simulation assumption, can expose real memory-model/library behavior, but failures are probabilistic and reports lack exact execution traces.

Use both for load-bearing primitives when model-check determinism and stress realism cover different risks.

## Scenario options

Defaults in current docs:
- iterations 100
- invocations per iteration 10,000
- threads 2
- actors before/per thread/after 5/5/5
- timeout 3000 ms
- model loop bound 50
- recursion bound 20
- loop iterations before switch 10 (must be below loop bound)

Start defaults. Constrain arguments first; then tune the dimension matching the bug. Excess threads/actors can explode state space and reduce useful depth.

Failed-scenario minimization removes irrelevant actors. Disable only temporarily to inspect context.

`stdLibAnalysisEnabled` defaults false; standard-library operations are treated thread-safe. `addGuarantee(...treatAsAtomic|ignore)` can reduce instrumentation. Each guarantee is a trusted assumption: scope class/method predicates narrowly and verify it cannot hide subject behavior.
