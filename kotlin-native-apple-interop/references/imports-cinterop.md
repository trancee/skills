# Objective-C/C imports and cinterop

Sources: [definition files](https://kotlinlang.org/docs/native-definition-file.html) and [C interop](https://kotlinlang.org/docs/native-c-interop.html).

Prefer pre-generated `platform.*` bindings for Apple system frameworks. Third-party bindings use CocoaPods or a Gradle `cinterops` configuration backed by `.def`.

## Definition file

Key properties:
- `modules` for Clang modules such as UIKit
- `headers` for explicit headers
- `language=Objective-C` when required
- `package` unique Kotlin package
- `headerFilter` narrow include globs; `excludeFilter` wins
- target-specific `compilerOpts.*` and `linkerOpts.*`
- `strictEnums`/`nonStrictEnums`, `noStringConversion`, `excludedFunctions`
- `disableDesignatedInitializerChecks` narrow workaround
- `foreignExceptionMode=objc-wrap` to wrap Objective-C exceptions
- `userSetupHint` for consumer linker guidance
- `staticLibraries`/`libraryPaths` experimental embedding

When the same cinterop is shared through an intermediate hierarchical source set such as `appleMain`, enable `kotlin.mpp.enableCInteropCommonization=true` and verify commonized bindings. Hiding the warning does not enable commonization.

Published configs must not contain developer-local absolute include/library paths. Generate bindings per target; IDE stubs do not prove final link.

## Memory/pointers

- `CPointer<T>?` represents nullable C pointers; `reinterpret` is unsafe
- `memScoped` owns temporary allocations lexically
- `nativeHeap` requires explicit free
- `CValuesRef` temporary copies live only through the call
- `StableRef` transfers Kotlin references through `void*`; dispose once after callback ownership ends
- `staticCFunction` callback cannot capture values
- C strings default UTF-8 conversion; `noStringConversion` exposes raw pointers

Use wrapper declarations for unsupported macros. Match struct-by-value `CValue` and pointer lifetime exactly.

## Pure Swift

Direct pure Swift import is unsupported. Options:
1. expose an Objective-C-compatible Swift API and import its module
2. write Objective-C wrappers plus `.def`
3. reverse import: Kotlin interface or closure implemented in Swift and injected into Kotlin; prefer interface for state/testability
