# Kotlin Multiplatform source sets

## Choose the source set

A source set defines source files, dependencies, compiler options, and the targets that compile it. Put code in the narrowest source set shared by every intended target:

- `commonMain` and `commonTest` compile for every declared target.
- A platform source set such as `jvmMain`, `jsMain`, or `linuxX64Main` can use that platform's APIs and dependencies.
- An intermediate source set such as `appleMain` shares code among a subset of targets.

Code in a platform source set can use declarations from its parent source sets. Common code cannot use a platform source set or a platform-only dependency. Read [Kotlin Multiplatform project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html) before moving files between source sets.

Keep platform suffixes on files that define top-level declarations in platform source sets, such as `Platform.jvm.kt`. Use an unsuffixed name in `commonMain`. This avoids duplicate JVM file facade names when common and JVM files share a package and base filename.

## Declare targets

Declare every produced platform in the `kotlin {}` block. A target controls the binary format, available APIs, compiler settings, and default source sets. Compile every affected target after changing a parent source set.

Apple device and simulator builds use separate targets. Shared iOS code normally belongs in `iosMain`, while `iosArm64Main` and `iosSimulatorArm64Main` contain code that differs between the device and simulator.

Use target-specific dependencies only in the source set that can compile them. A dependency added to `commonMain` must publish a compatible variant for every declared target.

## Bridge platform APIs

Prefer a common interface with platform implementations when normal dependency injection can supply the implementation. Use `expect` and `actual` when common code must name a platform-provided declaration directly.

For `expect` and `actual` declarations:

1. Put the `expect` declaration in a common or intermediate source set without an implementation.
2. Put a matching `actual` declaration in every leaf target or a suitable intermediate source set.
3. Keep the package, declaration kind, name, and compatible signature aligned.
4. Compile every target that must provide an `actual` declaration.

Prefer functions, properties, interfaces, and factory functions over expected classes where those forms fit. Expected classes remain Beta and require an explicit compiler opt-in. Read [Expected and actual declarations](https://kotlinlang.org/docs/multiplatform/multiplatform-expect-actual.html) before adding an expected class.

## Test shared code

Put target-independent contracts in `commonTest` and use `kotlin.test`. Put platform behavior in the matching platform test source set. Run the `<targetName>Test` task for each affected target. Native and Apple tests can require host-specific toolchains or simulators, so report any target that the current host cannot execute.

When shared code changes, a passing JVM test proves only the JVM compilation. Compile or test every target label attached to the changed source set.
