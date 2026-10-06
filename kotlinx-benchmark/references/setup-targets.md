# kotlinx-benchmark target setup

Source: [repository README](https://github.com/Kotlin/kotlinx-benchmark) and [JVM setup](https://github.com/Kotlin/kotlinx-benchmark/blob/master/docs/kotlin-jvm-project-setup.md).

Current 0.5.0 requires Kotlin 2.2.0+ and Gradle 8.0+. Align plugin/runtime versions; plugin from Gradle Plugin Portal, runtime from Maven Central. KSP-based analysis runs internally in standalone mode: do not add a consumer KSP plugin solely for benchmark generation.

## Kotlin Multiplatform

```kotlin
plugins {
    kotlin("multiplatform") version "<KOTLIN_VERSION>"
    id("org.jetbrains.kotlinx.benchmark") version "<BENCHMARK_VERSION>"
}

kotlin {
    jvm()
    js { nodejs() }
    sourceSets.commonMain.dependencies {
        implementation("org.jetbrains.kotlinx:kotlinx-benchmark-runtime:<BENCHMARK_VERSION>")
    }
}

benchmark {
    targets {
        register("jvm")
        register("js")
    }
}
```

Register exact Kotlin target/source-set names. Common benchmarks run on every registered target; platform-source benchmarks run only there.

## JVM/Java

Register `main` when benchmarks live in main, or a dedicated source set/compilation name. JVM uses JMH. Kotlin types are final by default; apply matching Kotlin all-open plugin and:
```kotlin
allOpen {
    annotation("org.openjdk.jmh.annotations.State")
}
```

A dedicated KMP compilation should `associateWith(main)` and register its default source-set name, e.g. `jvmBenchmark`. A dedicated Kotlin/JVM source set likewise needs an associated compilation and runtime dependency. Preserve existing source-set conventions.

## JS

Configure `js { nodejs() }`, then register the target name. Default executor uses benchmark.js; optional built-in executor supports `advanced("jsUseBridge", ...)`.

## Native

Create and register the Native target. Only the host target executes. Release build is default; `NativeBenchmarkTarget.buildType` can select debug for diagnosis, not comparable production measurement.

## Wasm

Wasm is experimental and tied to the release's build Kotlin version: 0.5.0 uses Kotlin 2.2.0. Configure wasmJs/wasmWasi Node execution and register the exact target; JVM/JS/Native consumer versions are not that exact Wasm requirement.
