---
name: kotlin-development
description: "Implements, reviews, builds, tests, and troubleshoots Kotlin projects across JVM, Android, Kotlin Multiplatform, JavaScript, Wasm, and Native. Use when editing Kotlin source, configuring Kotlin with Gradle or Maven, aligning Kotlin and JVM toolchains, working with coroutines or Java interop, or diagnosing compiler and test failures. Don't use for Java-only projects, Android UI work without Kotlin code, or build-system tasks unrelated to Kotlin."
metadata:
  source: "https://kotlinlang.org/docs/home.html"
  category: "development"
  sourceVersion: "Kotlin 2.4.10; Kotlin Help build 1155; Kotlin Multiplatform Help build 554"
  sourceBuiltAt: "2026-08-26"
  createdAt: "2026-08-30T10:56:53+02:00"
  updatedAt: "2026-08-30T11:05:26+02:00"
---

# Kotlin development

## Procedures

**Step 1: Bound the Kotlin task**

1. Identify whether the task changes Kotlin source, build configuration, tests, Java interop, coroutines, or Kotlin Multiplatform source sets.
2. Identify every affected module, target, public API, runtime, and minimum supported Kotlin, Java, Gradle, Maven, Android Gradle plugin, or native toolchain version.
3. Preserve the project's current build system, Kotlin version, language version, API version, plugin conventions, formatting, and test framework unless the request requires a migration.
4. Read the current [Kotlin documentation](https://kotlinlang.org/docs/home.html) and [Kotlin releases](https://kotlinlang.org/docs/releases.html) before changing versions or using a recently added API. Treat this skill as workflow guidance, not a version table.

**Step 2: Inspect the project before editing**

1. Run the project inspector from the target project root:

   ```bash
   python3 scripts/inspect-project.py --root . --json
   ```

2. Confirm the detected build system, wrapper, build files, Kotlin plugins, source sets, target declarations, and Kotlin file count against the repository.
3. Read `references/build-tools.md` for Gradle, Maven, compiler option, dependency, toolchain, or version work.
4. Read `references/multiplatform.md` when the project applies `org.jetbrains.kotlin.multiplatform`, uses target-specific source sets, or publishes more than one platform artifact.
5. Read `references/language-safety.md` when the change touches nullability, Java interop, coroutines, public APIs, or Kotlin style.
6. Read `references/testing.md` before adding tests or choosing validation tasks.

**Step 3: Establish the failing or required behavior**

1. Reproduce a reported compiler, test, runtime, or interop failure at the narrowest affected module and target. Treat a user-reported failure as established when the user already supplied the exact result.
2. For a feature, state the observable contract and identify the existing test layer that owns it.
3. Inspect compiler diagnostics at their source. Trace platform-type nullability, source-set visibility, coroutine cancellation, JVM target mismatch, and dependency resolution to the first failing boundary.
4. Separate source failures from build-tool, JDK, Gradle daemon, IDE, Android SDK, Xcode, Node.js, browser, or native linker failures before changing Kotlin code.

**Step 4: Make the smallest coherent change**

1. Put code in the narrowest source set that supports every intended caller. Keep platform APIs out of `commonMain`.
2. Preserve nullability in the type system. Replace an unsafe `!!` with a check, safe call, Elvis expression, or explicit boundary failure unless the invariant is proven at that line.
3. Keep Java platform types at the interop boundary. Add explicit Kotlin types or Java nullability annotations when inferred platform types could carry `null` into Kotlin code.
4. Keep coroutine work under an owned `CoroutineScope`. Preserve parent-child cancellation, rethrow `CancellationException`, and await every result whose failure matters.
5. Follow the repository's Kotlin style. Use the official [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html) only where the repository has no stricter formatter or convention.
6. Keep public API changes source-compatible and binary-compatible when the module promises compatibility. State any intentional break before implementing it.

**Step 5: Change build configuration only when required**

1. Use the checked-in Gradle or Maven wrapper. Do not replace it with a system installation.
2. Keep Kotlin Gradle plugin, Gradle, Android Gradle plugin, JDK, language, API, and JVM target versions compatible. Check the current official compatibility table before changing any one of them.
3. Configure Gradle compiler options through typed `compilerOptions {}` blocks. Keep broad defaults at the extension level and add target or task overrides only where behavior differs.
4. Align Kotlin and Java JVM targets with a Java toolchain or explicit matching targets. Do not silence JVM target validation.
5. Add dependencies to the source set or module that uses them. Preserve the version catalog, dependency management, and repository policy already in the project.
6. If a version migration is necessary, separate it from behavior changes when the repository can review and verify the two changes independently.

**Step 6: Add contract-level tests**

1. Add a test only when the changed observable contract lacks coverage.
2. Put shared Kotlin Multiplatform tests in `commonTest`. Put platform behavior in the matching target test source set.
3. Test coroutine completion, cancellation, failure propagation, and virtual time where those behaviors form the contract.
4. Test Java interop at the language boundary, including nullable platform values, collection mutability, checked exceptions, and generated JVM names when relevant.
5. Make the test fail for the original bug or missing behavior before accepting the implementation.

**Step 7: Run target-specific verification**

1. List available wrapper tasks before guessing a task name in an unfamiliar project.
2. Run the narrowest compile or test task for each changed source set and target.
3. Run the owning module's full test task after targeted checks pass.
4. Run the repository's formatter, linter, static analysis, API compatibility, and packaging checks when the changed module uses them.
5. For Kotlin Multiplatform, compile every target affected by shared code. Mark targets that the current host cannot build or run as unverified.
6. Exercise the changed runtime path. A successful compile alone does not prove coroutine, interop, serialization, UI, or native behavior.

**Step 8: Report exact completion evidence**

1. Copy `assets/completion-report.md` when the task needs a durable report.
2. Record changed modules, source sets, public APIs, build versions, commands, passed targets, produced artifacts, and unverified host-specific targets.
3. Report warnings and experimental APIs by exact diagnostic or opt-in marker. Do not describe a warning-free build when warnings were suppressed.
4. Remove disposable projects, generated archives, compiler output, and downloaded test artifacts that do not belong in the repository.

## Error Handling

- If the inspector reports both Gradle and Maven, identify the owning build before running commands. Do not update both by default.
- If no wrapper exists, use the repository's documented bootstrap path. Ask before generating or upgrading a wrapper.
- If Gradle reports incompatible Kotlin, Gradle, Android Gradle plugin, or JDK versions, use the current official compatibility table and change the smallest version boundary.
- If Kotlin and Java compilation tasks target different JVM versions, align them with the existing Java toolchain policy instead of disabling validation.
- If `commonMain` resolves a platform API only in the IDE, move the code to a platform source set or introduce a common interface with platform implementations.
- If a coroutine test hangs, inspect scope ownership, uncaught child failures, missing cancellation checks, and real dispatchers before adding a timeout.
- If the current host cannot run an Android, Apple, browser, Wasm, or native target, finish every available compile and test check and name the unverified target.
