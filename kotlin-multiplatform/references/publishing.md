# Multiplatform publication

Source: [Publishing setup](https://kotlinlang.org/docs/multiplatform/multiplatform-publish-lib-setup.html).

KMP with `maven-publish` creates:
- root `kotlinMultiplatform` publication (`group:artifact:version`) with metadata references
- one target publication, commonly suffixed (`artifact-jvm`, `artifact-iosarm64`, etc.)

Consumers depend on the root coordinate; Gradle metadata selects platform artifact. Publishing only root metadata leaves broken references.

## Workflow

1. set stable group/artifact/version
2. configure repository credentials outside source/logs
3. configure every target and Android publication explicitly
4. publish all root+target artifacts to local/disposable repository
5. resolve real consumers for common and each target
6. inspect POM, `.module`, variants/attributes, sources/docs, signatures/checksums
7. publish all coordinates from one host/workflow to avoid duplicates

`publishToMavenLocal`/`publishAllPublicationsTo<Repo>` are umbrella paths. Separate publication requires root plus every target.

Kotlin can produce Apple `.klib` artifacts from non-Mac hosts only when no cinterop/CocoaPods/final binary requirement blocks cross-compilation. Apple cinterop, CocoaPods, final frameworks, and tests need macOS. Use `kotlin-native-apple-interop` for framework distribution.

Android KMP library publication is not automatic; configure current `androidLibrary` publishing APIs. Sources are published by default and can be controlled through `withSourcesJar` globally/per target.

Publication compatibility includes KGP/metadata version, target set/names, source-set hierarchy, dependency scopes, native interop exposure, and binary ABI. Run dedicated ABI/Dokka checks where applicable.
