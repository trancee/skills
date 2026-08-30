# Spotless Gradle integration

Source: [Gradle plugin guide](https://github.com/diffplug/spotless/tree/main/plugin-gradle) and [changelog](https://github.com/diffplug/spotless/blob/main/plugin-gradle/CHANGES.md).

Current 8.10.1 requires JRE 17+ and, per the 8.1.0 changelog, Gradle 8.1+. Use 7.2.1 or older for JRE 11; 6.13.0 or older for JRE 8. Verify the live changelog before selecting a legacy line.

## Install

Kotlin DSL:
```kotlin
plugins {
    id("com.diffplug.spotless") version "<SPOTLESS_GRADLE_VERSION>"
}

spotless {
    format("misc") {
        target("*.gradle.kts", ".gitattributes", ".gitignore")
        targetExclude("build/**")
        trimTrailingWhitespace()
        endWithNewline()
    }
    java {
        googleJavaFormat("<FORMATTER_VERSION>")
    }
}
```

Preserve version catalogs and convention plugins. Android and `java-gradle-plugin` Java targets are not inferred reliably; configure `target("src/*/java/**/*.java")`. Generic and nonstandard language formats need explicit targets.

## Commands

- `./gradlew spotlessCheck`: all configured format checks
- `./gradlew spotlessApply`: mutate targets to canonical form
- `./gradlew spotlessJavaCheck` / `spotlessJavaApply`: one format
- `./gradlew check`: includes `spotlessCheck` by default
- `./gradlew :module:spotlessCheck`: exact multi-project owner
- `./gradlew spotlessApply -PspotlessFiles='regex,...'`: diagnostic subset; patterns use `String.matches` against absolute paths

`enforceCheck(false)` disconnects Spotless from `check`; flag it unless policy explicitly runs `spotlessCheck` separately.

## Multi-project and dependencies

Configure each owning project through the existing convention plugin. Root-only application does not automatically format subproject files. Use full task paths in multi-project or included builds.

Large parallel builds may predeclare formatter dependencies through root `spotlessPredeclare`; every formatter used below must be declared. Predeclaration is incompatible with Gradle isolated projects. Current Gradle plugin otherwise supports configuration cache and build cache.

Custom steps disable up-to-date/cache correctness unless their implementation version is bumped through the documented API.
