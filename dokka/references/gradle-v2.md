# Dokka Gradle plugin v2

Source: [Gradle guide](https://kotlinlang.org/docs/dokka-gradle.html) and [configuration options](https://kotlinlang.org/docs/dokka-gradle-configuration-options.html).

Current 2.2.0 minimums: Gradle 7.6, Kotlin Gradle plugin 1.9, Android Gradle plugin 7.0. Verify the live table before upgrades.

## Apply and generate

```kotlin
plugins {
    id("org.jetbrains.dokka") version "<DOKKA_VERSION>"
}

dokka {
    moduleName.set("Library")
    dokkaPublications.html {
        outputDirectory.set(layout.buildDirectory.dir("dokka/html"))
        failOnWarning.set(true)
    }
    dokkaSourceSets.configureEach {
        includes.from("MODULE.md")
        reportUndocumented.set(true)
    }
}
```

Tasks:
- `dokkaGenerate`: all formats from applied plugins; normal entry point
- `dokkaGeneratePublicationHtml`: HTML only; exposes output for task consumption
- `dokkaGeneratePublicationJavadoc`: Javadoc only
- `dokkaGenerateHtml`: IntelliJ-visible alias of HTML publication task

Apply `org.jetbrains.dokka-javadoc` at the same version to add Javadoc output. HTML is provided by `org.jetbrains.dokka`.

## Multi-project

Apply Dokka to every documentable child. Prefer the existing convention plugin for shared configuration. Aggregate in one project:
```kotlin
dependencies {
    dokka(project(":api"))
    dokka(project(":implementation"))
}
```

Root application alone does not document children. DGP v2 preserves full nested project paths in output; `modulePath` overrides only intentional URL compatibility.

## Source sets

Kotlin/Java/Android/KMP source roots, classpaths, display names, and platform are normally inferred from Kotlin/Android plugins. Configure `dokkaSourceSets.named("main")` or `configureEach` for policy; override roots/classpath only after proving inference is wrong.

DGP v2 supports Gradle build and configuration caches. Validate with the repository's cache flags after configuration changes.
