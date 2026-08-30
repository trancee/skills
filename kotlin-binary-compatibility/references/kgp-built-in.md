# Built-in Kotlin Gradle plugin ABI validation

Source: [Kotlin guide](https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html) and [KGP ABI API](https://kotlinlang.org/api/kotlin-gradle-plugin/kotlin-gradle-plugin-api/org.jetbrains.kotlin.gradle.dsl.abi/).

The DSL is experimental and available since KGP 2.2.0. Verify the live API for the repository's Kotlin version.

## Enable per module

```kotlin
kotlin {
    @OptIn(org.jetbrains.kotlin.gradle.dsl.abi.ExperimentalAbiValidation::class)
    abiValidation()
}
```

Configured form:
```kotlin
kotlin {
    @OptIn(org.jetbrains.kotlin.gradle.dsl.abi.ExperimentalAbiValidation::class)
    abiValidation {
        filters {
            excluded {
                byNames.add("**.InternalUtils")
                annotatedWith.add("com.example.InternalApi")
            }
            included {
                byNames.add("com.example.api.**")
            }
        }
    }
}
```

Tasks:
- `checkKotlinAbi`: compare current ABI with reference dumps; added to `check`
- `updateKotlinAbi`: overwrite reference dumps with current ABI

Run update and check in separate Gradle invocations. With KGP 2.4.10 and Gradle 9.6.1, requesting both together triggers Gradle implicit-dependency validation because the check consumes the update output in the same task graph.

Useful extension properties include `enabled`, `referenceDumpDir`, `filters`, `keepLocallyUnsupportedTargets`, `binariesSource`, variants, and task providers.

## Filters

`byNames` accepts `**` across periods, `*` within one name segment, and `?` for one character. `annotatedWith` requires BINARY or RUNTIME annotation retention. Exclusions win; with inclusion rules, a declaration must match one or contain a matching member.

## Binary source

Default/main compilation behavior follows the current plugin. `BinariesSource` supports `MAIN_COMPILATION`, `NON_TEST_COMPILATIONS`, and `MAVEN_PUBLICATIONS`. Maven publications require `maven-publish` and correctly configured publications. Kotlin/Android and KMP-with-Android projects do not publish JARs, so the documented Maven-publication path does not apply.

Never update reference dumps as an automatic CI repair. The update task accepts a reviewed API decision; it does not establish compatibility.
