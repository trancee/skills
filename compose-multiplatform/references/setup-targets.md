# Setup, compatibility, and targets

Sources: [compatibility and versions](https://kotlinlang.org/docs/multiplatform/compose-compatibility-and-versioning.html) and [Compose compiler migration](https://kotlinlang.org/docs/multiplatform/compose-compiler.html).

Version owners:
- `org.jetbrains.compose`: Compose Multiplatform release (current 1.12.0)
- `org.jetbrains.kotlin.multiplatform`: Kotlin/KMP release
- `org.jetbrains.kotlin.plugin.compose`: exactly the Kotlin/KMP version

Compose 1.12 deprecates `compose.runtime`, `compose.foundation`, `compose.material3`, `compose.components.resources`, `compose.uiTest`, and similar dependency accessors. Declare the direct coordinates/versions from the release component table; Material3, lifecycle, and navigation versions can differ from the Compose plugin.

Current direct examples:
```kotlin
commonMain.dependencies {
    implementation("org.jetbrains.compose.runtime:runtime:1.12.0")
    implementation("org.jetbrains.compose.foundation:foundation:1.12.0")
    implementation("org.jetbrains.compose.material3:material3:1.12.0-alpha03")
    implementation("org.jetbrains.compose.components:components-resources:1.12.0")
}
commonTest.dependencies {
    implementation("org.jetbrains.compose.ui:ui-test:1.12.0")
}
```
Refresh every coordinate from the same release table during upgrades; do not derive Material3/lifecycle/navigation versions from the Compose plugin version.

Apply both Compose plugins to every module that uses Compose. Since Compose 1.6.10/Kotlin 2.0, use the Kotlin Compose compiler Gradle plugin and `composeCompiler {}` options; remove legacy compiler artifact coordinates/options.

Compose 1.12.0 supported floors:
- Android 5/API 21
- iOS 14
- macOS 13 arm64
- Windows 10 x86-64/arm64
- Ubuntu 20.04 x86-64/arm64
- browsers with WasmGC

It requires Kotlin 2.1+; use 2.2.20+ for rapidly evolving iOS/web support. Apply the live KMP Gradle/AGP/Xcode compatibility tuple too.

Every target needs a platform entry point:
- Android: `ComponentActivity`/`setContent`
- iOS: `ComposeUIViewController` exported to Swift/SwiftUI/UIKit shell
- desktop JVM: `application`/`Window` or `singleWindowApplication`
- web JS/Wasm: target `main` attaching Compose to the page/viewport

Desktop runtime requires JDK 11+, and `jpackage` native distribution requires JDK 17+. Hot Reload is JVM-only. iOS requires macOS/Xcode for final build/run. Web compatibility mode emits JS+Wasm via `composeCompatibilityBrowserDistribution`.

Compose Android uses Google-published Jetpack artifacts selected by the Compose Multiplatform release. Do not force every AndroidX artifact to the Compose plugin version; use the live component table.
