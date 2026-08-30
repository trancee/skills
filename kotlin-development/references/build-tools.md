# Kotlin build tools

Read the sections that match the detected build. Preserve the repository's wrapper, DSL, plugin aliases, and dependency policy.

## Gradle

Use `./gradlew` or `gradlew.bat` when the repository contains a wrapper. Inspect `settings.gradle.kts`, each affected `build.gradle.kts`, `gradle.properties`, and `gradle/libs.versions.toml` before editing versions.

The current compatibility table lives in [Configure a Gradle project](https://kotlinlang.org/docs/gradle-configure-project.html). Check it when changing the Kotlin Gradle plugin, Gradle, or Android Gradle plugin. A newer version outside the fully supported range can compile with warnings or lose features, so a successful dependency resolution is not enough.

Use `compilerOptions {}` for compiler settings. The older `kotlinOptions {}` form is deprecated. Put common settings in `kotlin.compilerOptions`, target-specific settings in the target block, and task-specific exceptions on the compilation task. Lower levels override higher levels.

For JVM modules, prefer the repository's Java toolchain declaration. A toolchain sets the JDK used by Java tasks and supplies the Kotlin compiler's JDK and default `jvmTarget`. Keep Kotlin `jvmTarget` and Java `targetCompatibility` aligned. Gradle 8 and later fail mismatches by default.

Discover tasks before selecting one:

```bash
./gradlew tasks --all
./gradlew projects
```

Use the smallest owning task first. Common JVM checks include `compileKotlin`, `compileTestKotlin`, `test`, `check`, and `build`. Android and Kotlin Multiplatform task names include variants or target names. Use task output from the project instead of constructing a name from memory.

Use `--stacktrace` for the failing task. Use `--info` or `--debug` only when resolution or compiler arguments remain unclear. Gradle debug logs expose `Kotlin compiler args:` for JVM, JavaScript, and Wasm tasks and `Arguments =` for Native tasks.

## Maven

Kotlin Maven projects target the JVM. Use `./mvnw` or `mvnw.cmd` when present. Inspect `pom.xml`, parent dependency management, profiles, and the `kotlin-maven-plugin` before changing source roots or versions.

Keep the Kotlin plugin version and Kotlin standard library version aligned through the project's existing property or dependency management. Preserve plugin execution order in mixed Kotlin and Java modules. Run the Kotlin compilation before Java compilation when both languages depend on Kotlin declarations.

Typical verification commands are:

```bash
./mvnw test
./mvnw verify
```

Select the affected module with the repository's existing Maven module pattern. Do not add a second version property when a parent or bill of materials already controls Kotlin dependencies.

## Standalone compiler

Use `kotlinc` for a small standalone program, a script, or a reduced compiler reproduction. Build managed applications and libraries with their checked-in build system.

Compile and run a self-contained JVM program with:

```bash
kotlinc Main.kt -include-runtime -d app.jar
java -jar app.jar
```

Compile a library without `-include-runtime`. Its consumer must provide the Kotlin runtime. Inspect current options with `kotlinc -help`; advanced `-X` options can change without compatibility guarantees.

## Version changes

Read [Kotlin releases](https://kotlinlang.org/docs/releases.html) and the migration guide for the destination language release. Update kotlinx libraries and compiler plugins only when their compatibility requires it. Keep a behavior fix separate from a Kotlin upgrade unless the old compiler is the cause.

Do not copy the latest version from this reference. The Kotlin documentation homepage observed during authoring reported Kotlin 2.4.10 on 2026-08-30, but the live release and compatibility pages are authoritative.
