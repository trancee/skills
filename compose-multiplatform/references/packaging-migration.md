# Packaging, release, and migration

Source: [compatibility and versions](https://kotlinlang.org/docs/multiplatform/compose-compatibility-and-versioning.html), [first app](https://kotlinlang.org/docs/multiplatform/compose-multiplatform-create-first-app.html), and [compiler migration](https://kotlinlang.org/docs/multiplatform/compose-compiler.html).

Run/package the owning platform app, not only the shared library:
- Android: release variant/bundle, resources, minification, signing, install
- iOS: framework/Xcode app, resources, signing, simulator/device on macOS
- desktop: runtime app plus native distributions using JDK 17+ `jpackage`
- web: production JS/Wasm distribution served over HTTP; compatibility distribution when fallback required

Inspect Gradle tasks from the checked-in wrapper because module/target names change task names. Smoke the packaged artifact on every supported architecture/OS/browser tier.

Upgrade sequence:
1. read Compose release notes and live compatibility/platform tables
2. align Kotlin/KMP with `org.jetbrains.kotlin.plugin.compose`
3. update `org.jetbrains.compose` and independent lifecycle/navigation/resource/testing artifacts
4. remove legacy Compose compiler coordinates/options and deprecated APIs
5. clean stale build directories only when migration causes generated-resource/compiler cache mismatch
6. compile common code and every target
7. run shared/platform UI tests and real surfaces
8. build/install/serve release artifacts

Compose 1.8+ is K2-only and requires Kotlin 2.1+. Avoid `disableNativeCache` unless the documented older-library compatibility workaround is necessary; it increases build time and hides dependency migration debt.

Previews and Hot Reload accelerate iteration only. Preview dependencies/configuration must be explicit, and Hot Reload verifies JVM behavior—not iOS/Android/web release behavior.
