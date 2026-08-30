# Consumer setup and configuration

Sources: [quickstart](https://kotlinlang.org/docs/ksp-quickstart.html), [google/ksp README](https://github.com/google/ksp), and [KSP 2.3.0 release](https://github.com/google/ksp/releases/tag/2.3.0).

Current plugin:
```kotlin
plugins {
    kotlin("jvm") version kotlinVersion
    id("com.google.devtools.ksp") version "2.3.11"
}

dependencies {
    implementation(project(":annotations"))
    ksp(project(":processor"))
    // kspTest(project(":test-processor"))
}

ksp {
    arg("schemaDir", layout.projectDirectory.dir("schemas").asFile.path)
}
```

KSP 2.3+ versioning is independent from Kotlin's old `<kotlin>-<ksp>` format. KSP2 is no longer a compiler plugin; KSP1 has been removed. Still verify the release against exact Kotlin/KGP/AGP/Gradle through a real build.

Processor configuration controls which compilation runs it; `implementation` controls generated/runtime API dependencies and does not run the processor. Keep processor artifacts off runtime unless they intentionally provide runtime classes.

KSP auto-registers generated Kotlin/Java/resource output with owning compilation. Manual `srcDir("build/generated/ksp/...")` commonly causes duplication/stale paths.

Options are Gradle task inputs. Make paths relocatable, values stable, and secrets absent. Read options from `SymbolProcessorEnvironment.options`; reject missing/invalid required options with actionable diagnostics.
