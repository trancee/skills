# Serialization setup and platforms

Sources: [setup tutorial](https://kotlinlang.org/docs/serialization-get-started.html) and [repository README](https://github.com/Kotlin/kotlinx.serialization).

Compiler plugin and runtime versions are independent:
```kotlin
plugins {
    kotlin("jvm") version "<KOTLIN_VERSION>"
    kotlin("plugin.serialization") version "<KOTLIN_VERSION>"
}

repositories { mavenCentral() }

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:<RUNTIME_VERSION>")
}
```

Current runtime 1.11.0 is built with Kotlin 2.3.20. Verify compatibility with the project's Kotlin version. `kotlinx-serialization-json` transitively supplies core; use core alone only without a format.

KMP adds the base format artifact to `commonMain`; Gradle selects JVM/JS/Native variants. Keep platform-only APIs in platform source sets.

Maven adds `kotlinx-serialization` to `compilerPlugins`, `org.jetbrains.kotlin:kotlin-maven-serialization` matching `${kotlin.version}`, and format runtime using independent `${serialization.version}`.

## Format stability

- JSON: stable, all supported platforms
- HOCON: experimental, JVM only
- ProtoBuf: experimental, all supported platforms
- CBOR: experimental, all supported platforms
- Properties: experimental, all supported platforms
- custom formats/encoder APIs: experimental

Require exact-version API review and local opt-in for experimental APIs.

## Android shrinking

Bundled rules retain serializers for retained serializable classes. Named companion objects require additional class/InnerClasses keep rules, differing between ProGuard/R8 compatibility and full mode. Exercise a minified release build and real encode/decode; debug success is insufficient.
