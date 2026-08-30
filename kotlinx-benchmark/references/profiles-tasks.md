# Profiles, tasks, and reports

Source: [configuration options](https://github.com/Kotlin/kotlinx-benchmark/blob/master/docs/configuration-options.md) and [task overview](https://github.com/Kotlin/kotlinx-benchmark/blob/master/docs/tasks-overview.md).

## Profiles

`main` exists by default. Add a short diagnostic profile:
```kotlin
benchmark {
    configurations {
        named("main") {
            warmups = 10
            iterations = 10
            iterationTime = 1
            iterationTimeUnit = "s"
            reportFormat = "json"
        }
        register("smoke") {
            include(".*CriticalBenchmark.*")
            warmups = 0
            iterations = 1
            iterationTime = 100
            iterationTimeUnit = "ms"
        }
    }
}
```

Options: `iterations` positive; `warmups` nonnegative; `iterationTime` positive; `iterationTimeUnit`; `outputTimeUnit`; `mode` (`thrpt`/Throughput or `avgt`/AverageTime); regex `include`/`exclude`; `param`; report `json` default, `csv`, `scsv`, or `text`.

Time units accept ns/nanos, us/micros, ms/millis, s/sec, m/min and full names.

## Generated tasks

For target `jvm` and profile `smoke`:
- `benchmark`: main profile, all targets
- `jvmBenchmark`: main profile, one target
- `smokeBenchmark`: smoke profile, all targets
- `jvmSmokeBenchmark`: smoke profile, one target
- `jvmBenchmarkJar`: self-contained JVM/JMH JAR under `build/benchmarks/jvm/jars/`

Use full module task paths in multi-project builds. List tasks after configuration; target/compilation names determine exact spelling.

## JVM advanced options

- `advanced("jvmForks", n)`: default 1; 0 disables forks; `definedByJmh` uses `@Fork`/JMH default
- `advanced("jmhIgnoreLock", true)`: sets JMH lock property
- `JvmBenchmarkTarget.jmhVersion`: default 1.37 in 0.4.19; multiple JVM targets with different JMH versions are unsupported

## Platform options

Native: `nativeFork=perBenchmark|perIteration`, `nativeGCAfterIteration`; release build default. JS/Wasm: `jsUseBridge` default true for built-in executor.

Treat result files as immutable raw evidence. Record task/profile/target/parameters alongside the report because filenames alone may not encode the full invocation.
