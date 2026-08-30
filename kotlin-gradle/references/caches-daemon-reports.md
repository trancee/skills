# Kotlin compilation, caches, daemon, and reports

Source: [compilation and caches](https://kotlinlang.org/docs/gradle-compilation-and-caches.html) and [execution strategy](https://kotlinlang.org/docs/compiler-execution-strategy.html).

## Incremental and Gradle caches

Kotlin/JVM and JS incremental compilation is enabled by default. JVM uses fine-grained source/class snapshots and coarse-grained cached-JAR ABI snapshots. Disabling via `kotlin.incremental=false` or `kotlin.incremental.js=false` invalidates incremental caches; the first build is never incremental. Use only as a diagnostic comparison.

Kotlin tasks support Gradle build cache. `-Dkotlin.caching.enabled=false` disables it globally and is diagnostic, not a fix. Configuration cache is used automatically when enabled; run the same task twice and require reuse.

## Compiler execution

- `daemon`: default, fastest, separate Kotlin daemon
- `in-process`: compiler inside Gradle process, simpler memory model, less isolation

Set `kotlin.compiler.execution.strategy=daemon|in-process`; task property overrides. The Kotlin daemon uses the Gradle daemon JDK.

Daemon argument precedence rises through inherited Gradle args, `kotlin.daemon.jvm.options`, `kotlin.daemon.jvmargs`, Kotlin extension, task. Different argument sets can start multiple Kotlin daemons.

Fallback to in-process is default when daemon communication fails. Set `kotlin.daemon.useFallbackStrategy=false` when CI must fail rather than silently change execution/resource behavior.

## Build reports

Use `kotlin.build.report.output=file|single_file|build_scan|http|json` combinations. Required companion paths:
- `single_file` -> `kotlin.build.report.single_file`
- `json` -> `kotlin.build.report.json.directory`
- file directory -> `kotlin.build.report.file.output_dir`

Reports expose compiler version, phase durations, and non-incremental reasons. HTTP reports can include project/system properties containing paths or secrets; disable verbose environment collection unless approved. Never print/report HTTP credentials.
