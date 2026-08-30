# Kover Gradle

Source: [Gradle plugin](https://kotlin.github.io/kotlinx-kover/gradle-plugin/). Live release may exceed examples.

## Coverage scope

- JVM: JVM/Java tests
- KMP: common+JVM code exercised by JVM tests; JS/Native ignored
- Android: local JVM unit tests; on-device instrumentation unsupported
- mixed Kotlin+Java supported

Apply `org.jetbrains.kotlinx.kover` version in root/owning modules. Multi-module: root merger recommended; submodules may omit version after root declaration. Maven Central required.

## Tasks

Total: `koverHtmlReport`, `koverXmlReport` (JaCoCo-compatible), `koverBinaryReport` (IC), `koverLog`, `koverVerify`.
Named report variant appends capitalized name: `koverHtmlReportRelease`, `koverVerifyCustom`. Report task runs included tests automatically.

Android report variants map build variants; total combines all. KMP mixed Android/JVM can create custom variant:
```kotlin
kover {
    currentProject {
        createVariant("custom") {
            add("debug")
            add("jvm")
        }
    }
}
```

## Reports

```kotlin
kover {
    reports {
        total {
            html { htmlDir = layout.buildDirectory.dir("reports/kover/html") }
            xml { xmlFile = layout.buildDirectory.file("reports/kover/report.xml") }
        }
    }
}
```
`onCheck=true` attaches report/verification behavior to `check` where configured.

## Engine

Default embedded Kover engine. Alternative:
```kotlin
kover { useJacoco("<VERSION>") }
```
JaCoCo feature parity is incomplete; annotation/inheritance filters differ. All merged projects must use one engine.

## Prototype aggregation plugin

`org.jetbrains.kotlinx.kover.aggregation` is a preliminary Settings plugin. It includes only classes compiled and tests run in the same invocation with `-Pkover`; DSL can break without compatibility. Use only explicit prototype/test request, never default production setup.
