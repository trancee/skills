# SKIE install/config

## Placement/repositories

Apply `co.touchlab.skie` only in KMP modules creating Xcode frameworks (`framework {}` or `kotlin("native.cocoapods")`). All declarations exported into that framework, including exported dependencies, are processed.

Plugin published to Maven Central. If plugin resolution lacks it:
```kotlin
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
```
Use current version from [Installation](https://skie.touchlab.co/Installation)+[changelog](https://skie.touchlab.co/category/changelog).

## Rule precedence

```kotlin
import co.touchlab.skie.configuration.FlowInterop

skie {
    features {
        group { FlowInterop.Enabled(false) }
        group("com.example.api") { FlowInterop.Enabled(true) }
    }
}
```
`group` argument=fully-qualified-name prefix, not exact class selector. Last matching value wins. Add a later narrower group to undo accidental prefix matches.

Annotation config overrides Gradle config by default. `group("prefix", overridesAnnotations = true)` reverses that precedence for matching declarations.

Owned declaration annotation example:
```kotlin
import co.touchlab.skie.configuration.annotations.FlowInterop

@FlowInterop.Enabled
fun values(): Flow<Int> = flowOf(1)
```
Add matching version where annotations compile:
```kotlin
commonMain.dependencies {
    implementation("co.touchlab.skie:configuration-annotations:<SKIE_VERSION>")
}
```
Dependencies/exported external code require Gradle config.

## Feature switches

Defaults at SKIE 0.10.14 snapshot:
- `EnumInterop.Enabled(true)`; `LegacyCaseName(false)`
- `SealedInterop.Enabled(true)`; `ExportEntireHierarchy(true)`
- `FunctionInterop.FileScopeConversion.Enabled(true)`; `LegacyName(false)`
- `features.coroutinesInterop=true`; prerequisite only
- `SuspendInterop.Enabled(true)`
- `FlowInterop.Enabled(true)`
- `DefaultArgumentInterop.Enabled(false)`; max default args=5

Disable entire plugin without deleting config:
```kotlin
skie { isEnabled.set(false) }
```

## Analytics

Upload off, local JSON retained:
```kotlin
skie { analytics { disableUpload.set(true) } }
```
Capture+upload off:
```kotlin
skie { analytics { enabled.set(false) } }
```
With upload disabled, inspect `build/skie/<framework>/<architecture>/analytics` after link task. Fine-grained flags: `additionalConfigurationFlags`, `suppressedConfigurationFlags`; read [Analytics](https://skie.touchlab.co/Analytics).

## Distributable framework

Default framework is non-distributable. Binary distribution to other machines:
```kotlin
skie { build { produceDistributableFramework() } }
```
This enables Swift library evolution, no Clang module breadcrumbs for static frameworks, and relative project source paths. Read [Swift compiler config](https://skie.touchlab.co/configuration/swift-compiler) before overriding components.
