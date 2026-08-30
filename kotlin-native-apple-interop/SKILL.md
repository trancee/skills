---
name: kotlin-native-apple-interop
description: "Configures, implements, and troubleshoots Kotlin/Native interoperability with Swift, Objective-C, and Apple frameworks. Use when producing frameworks or XCFrameworks, exporting Kotlin APIs, consuming Objective-C or C libraries through cinterop or CocoaPods, mapping names, types, blocks and errors, managing ARC/GC lifetimes, stabilizing native imports, or diagnosing header and linker failures. Don't use for SKIE-specific generated Swift APIs, Swift-only implementation, generic multiplatform architecture, Android JNI, or non-Apple native interop."
compatibility: "Apple framework linking, cinterop against Apple SDKs, Xcode integration, and Swift consumer verification require macOS with a Kotlin-compatible Xcode. Native library import is Beta. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/native-objc-interop.html"
  sourceVersion: "Kotlin 2.4.10; Kotlin Help build 1155; Apple framework and native import docs 2026"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T15:28:38+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T15:28:38+02:00"
---

# Kotlin/Native Apple interop

## Step 1: Establish direction and artifact

1. DEFINE export Kotlin framework | XCFramework | Xcode integration | import Objective-C/C | pure Swift workaround | API mapping | memory/error issue | compatibility migration.
2. IDENTIFY framework-producing KMP module, Apple targets/architectures, Kotlin/Xcode/Swift/Gradle versions, deployment targets, static/dynamic choice, integration/distribution method, imported native libraries, and Swift/Objective-C consumers.
3. READ the current [Swift/Objective-C interop](https://kotlinlang.org/docs/native-objc-interop.html), [Apple framework](https://kotlinlang.org/docs/apple-framework.html), and [native import stability](https://kotlinlang.org/docs/native-lib-import-stability.html) pages before API/toolchain changes.
4. REQUIRE macOS and a supported Xcode for Apple linking, cinterop, and Swift verification. On other hosts, finish static configuration checks and mark artifact/runtime behavior unverified.
5. ROUTE SKIE-specific suspend/Flow/enum/sealed transformations to `skie`; keep this skill on compiler-native Objective-C bridge behavior.

Completion: direction, module, targets, artifact, consumer, distribution, deployment floor, and compatible toolchain are explicit.

## Step 2: Inspect configuration and exported API

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM Apple targets/frameworks/XCFrameworks, base names/static mode/exports, CocoaPods/cinterops, `.def` properties, linker/compiler options, package names, binary options, export annotations, native types in public signatures, StableRef/native allocation balance, and strong-link candidates. Inspect generated Gradle task names afterward.

Completion: every framework/import/consumer edge has an owning configuration and exact task.

## Step 3: Align Kotlin, Xcode, and deployment targets

READ `references/stability-toolchains.md`.

1. SELECT the Kotlin-recommended Xcode version; local header import uses the installed Xcode SDK.
2. CHECK third-party headers/modules against that Xcode and every deployment target.
3. PREVENT strong references to unavailable Objective-C classes with a Swift/Objective-C availability wrapper; Kotlin guards cannot prevent launch-time strong-link failure.
4. Keep Kotlin/compiler/Xcode versions recorded with produced klibs/frameworks; do not mix unexplained artifacts across toolchain versions.

Completion: headers/platform libraries/imported klibs and deployment availability agree on one tested toolchain matrix.

## Step 4: Configure frameworks and XCFrameworks

READ `references/frameworks-distribution.md`.

1. DECLARE `binaries.framework` for every intended Apple target with identical stable `baseName`.
2. SELECT static/dynamic form from consumer/distribution requirements.
3. ADD each slice to `XCFramework` when distributing multiple platforms/architectures.
4. EXPORT only explicit `api` dependencies needed in Swift/Objective-C; avoid `transitiveExport` unless full transitives are deliberate.
5. SET Info.plist binary options and KDoc export policy explicitly when part of distribution contract.

Completion: debug/release framework and XCFramework tasks map to every required slice and exported module.

## Step 5: Design the exported Kotlin API

READ `references/export-mappings.md`.

1. INSPECT the generated Objective-C header/Swift interface; never guess translated names or types.
2. USE `@ObjCName` for stable consumer-facing names, `@HiddenFromObjC` for Kotlin-public implementation API, and `@ShouldRefineInSwift` for deliberate Swift wrappers.
3. ADD `@Throws` for expected non-suspend exceptions that must cross as NSError/Error; all others terminate if they escape.
4. ACCOUNT for boxed nullable primitives, collection/string copies, function-type boxing/Unit, generic erasure/nullability, enums as classes, top-level `*Kt` containers, and unsupported inline classes.
5. Avoid same-named exported classes across Kotlin packages because Objective-C has no package namespaces and collision renaming is unstable.

Completion: generated header/interface is reviewed as the actual public Apple API.

## Step 6: Import Objective-C/C libraries

READ `references/imports-cinterop.md`.

1. USE prebuilt `platform.*` libraries for Apple system frameworks where available.
2. For third-party libraries, define one direct CocoaPods/cinterop owner with a unique package name.
3. NARROW `.def` headers/modules using `headerFilter`/`excludeFilter`; configure platform-specific compiler/linker options without machine-local paths in published metadata.
4. REGENERATE bindings per target and verify actual link, not only IDE stubs.
5. For pure Swift without Objective-C export, prefer reverse import through a Kotlin interface/closure implemented in Swift; otherwise write an Objective-C wrapper plus `.def`.

Completion: generated Kotlin bindings compile and link against the intended library/SDK on each Apple target.

## Step 7: Control native import stability

1. AVOID native types in public Kotlin library APIs unless the library intentionally extends that native API.
2. DECLARE third-party native interop directly instead of relying on transitive exposure; Kotlin/Native treats native dependencies as API.
3. ASSIGN unique `packageName` for CocoaPods/cinterop to prevent binding/package/symbol collisions.
4. AVOID embedding static libraries into published klibs when consumers may need to replace/deduplicate them.
5. REGENERATE and diff bindings/framework headers across Kotlin/Xcode upgrades before source changes.

Completion: consumers are not coupled accidentally to transitive native bindings, local paths, or unreplaceable static binaries.

## Step 8: Handle memory, callbacks, and exceptions

READ `references/memory-errors.md`.

1. BOUND native allocations with `memScoped` or pair `nativeHeap` allocation/free.
2. PAIR every `StableRef.create` with one lifetime-defined `dispose`; never use the pointer afterward.
3. MODEL Swift/Objective-C retain cycles explicitly; mixed cycles containing Objective-C objects are not reclaimed automatically.
4. USE autorelease pools around long Kotlin loops creating temporary Objective-C objects when measured stable refs/memory grow.
5. VERIFY callback/function-block lifetime, thread, boxing, and exception path; suspend completion may run off Main.

Completion: ownership/release/thread/error policy exists for every object or callback crossing the boundary.

## Step 9: Integrate and build

READ `references/integration-verification.md`.

1. RUN target-specific debug framework link first, then release and XCFramework/distribution tasks.
2. INTEGRATE through the repository's chosen direct/Xcode, CocoaPods, or SwiftPM path; do not layer methods.
3. COMPILE the real Swift/Objective-C consumer against generated output.
4. TEST deployment-minimum device/simulator, exported API calls, exceptions, suspend callbacks, callbacks, and memory lifecycle.
5. SNAPSHOT/diff header/Swift interface and artifact contents for upgrades.

Completion: actual consumer builds, links, launches, and exercises the boundary on every supported slice.

## Step 10: Report completion

COPY `assets/interop-report.md`; fill toolchain/targets, framework/import graph, tasks/artifacts, header/API mapping, deployment/strong links, cinterop config, memory/error tests, consumer results, and host limitations.

## Error Handling

- Framework task missing -> verify Apple target and `binaries.framework`; `embedAndSignAppleFrameworkForXcode` registers only with framework configuration.
- `Framework not found`/undefined symbol -> inspect linker options, native dependency installation, architecture, package duplication, and user setup hint.
- Symbol not found at launch -> strong-linked API exceeds deployment OS; use an availability-checking Swift/Objective-C wrapper.
- cinterop header/type changes after upgrade -> align Kotlin/Xcode, narrow header filters, regenerate bindings, and compare generated API.
- Duplicate global/package symbols -> configure a unique interop package and remove duplicate transitive/direct binding.
- Swift cannot import pure Swift dependency in Kotlin -> use Objective-C-exposed wrapper or reverse-import interface/closure.
- Exception terminates process -> declare exact expected `@Throws` hierarchy or contain it before export; never export arbitrary exceptions.
- Memory grows across boundary -> inspect stable refs, autorelease pools, mixed retain cycles, and GC logs before adding manual lifetime hacks.
