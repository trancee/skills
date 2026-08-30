# Native import stability and toolchains

Source: [C, Objective-C, and Swift library import](https://kotlinlang.org/docs/native-lib-import-stability.html).

C/Objective-C import is Beta. Kotlin version changes the shipped platform libraries and native-to-Kotlin translation. For Apple targets, platform libraries are generated from the Xcode version supported by that compiler.

Third-party headers usually include Xcode system headers, so local Xcode affects cinterop output. Use the Kotlin-recommended Xcode version from the live KMP compatibility table. Newer Xcode can break import completely; older Xcode can generate missing or leaked system types.

Cross-compiling Apple targets with third-party native imports from non-macOS hosts is unsupported because the Apple/Xcode headers are required.

## Strong linking

Referencing an Objective-C class creates a strong external symbol. If that class is absent on the deployment OS, the app can crash at launch even when guarded code never runs. Kotlin availability checks are too late. Hide the symbol behind a Swift/Objective-C wrapper that checks availability without placing the unavailable class in Kotlin-linked API.

## Published libraries

Kotlin/Native does not distinguish API from implementation for native dependencies; transitive native bindings leak. Configure the same library directly with a unique package instead of relying on a transitive binding.

Avoid native types in public Kotlin API unless extending that native library is the product. Avoid embedding static libraries in klibs: consumers cannot replace/exclude/deduplicate them. Record Kotlin, Xcode, SDK, target, deployment floor, header version, compiler/linker flags, and binding package with every publication.

Before upgrades: generate bindings/framework headers with old/new toolchains from unchanged source and diff. A successful local compile on an older Xcode does not guarantee downstream binary compatibility when native types leak into public APIs.
