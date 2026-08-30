# detekt Gradle/CLI

## Version tracks

| track | plugin ID | coordinates/packages | status at source snapshot |
|---|---|---|---|
| 2.x | `dev.detekt` | `dev.detekt:*`, `dev.detekt.*` | `2.0.0-alpha.6`, prerelease |
| 1.x | `io.gitlab.arturbosch.detekt` | `io.gitlab.arturbosch.detekt:*` | `1.23.8`, stable |

Live [compatibility](https://detekt.dev/docs/introduction/compatibility) wins. Snapshot alpha.6 built with Kotlin 2.4.10, Gradle 9.6.1, AGP 9.3.1, tested JDK 25. Do not infer minimums from build tuple.

## Gradle

2.x:
```kotlin
plugins { id("dev.detekt") version "<VERSION>" }
repositories { mavenCentral() }
detekt {
    toolVersion = "<VERSION>"
    config.setFrom(file("config/detekt/detekt.yml"))
    buildUponDefaultConfig = true
    allRules = false
}
```
1.x uses `io.gitlab.arturbosch.detekt` and matching imports/artifacts.

Discover tasks:
```bash
./gradlew tasks --all
```
Core: `detekt`, `detektGenerateConfig`, `detektBaseline`; JVM `detektMain/Test`; Android `detekt<Variant>`; KMP names from `references/type-resolution-ci.md`. `check` depends on `detekt` by default.

Reports 2.x:
```kotlin
tasks.withType<dev.detekt.gradle.Detekt>().configureEach {
    reports {
        checkstyle.required.set(true)
        html.required.set(true)
        sarif.required.set(true)
        markdown.required.set(true)
    }
}
```
1.x names: `xml`, `html`, `sarif`, `md`; task class legacy package.

## Config

Generate once: `./gradlew detektGenerateConfig`. Custom config replaces defaults unless `buildUponDefaultConfig=true`. Keep project overrides only when building on defaults. `config.validation=true`; `warningsAsErrors` per policy. Custom property paths require `config.excludes` entries. `allRules` includes unstable rules; default false.

`failOnSeverity`: `Error|Warning|Info|Never`. `ignoreFailures=true` disables task failure. Set either only from explicit CI policy.

## CLI

Use release-matched CLI; full/type-aware analysis needs `--analysis-mode full --classpath ... --jvm-target ...` plus matching language/API/JDK options.

Exit: `0` clean; `1` internal/unexpected; `2` findings; `3` invalid config. Reports: `--report id:path`; 2.x IDs `checkstyle|html|md|sarif` per current CLI help (verify exact release); inspect `detekt --help` rather than cache flags here.
