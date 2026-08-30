# Apple integration and verification

## Build sequence

1. list target/framework tasks
2. link one debug framework per target
3. inspect framework binary, Headers, Modules, Info.plist
4. compile Swift/Objective-C smoke consumer
5. link release slices
6. assemble XCFramework/fat framework if required
7. integrate/sign/embed through selected distribution path
8. run minimum-OS device and simulator scenarios

Framework headers are target-independent in intent; compare slices and fail on drift.

## Integration methods

Direct Xcode integration uses `:<module>:embedAndSignAppleFrameworkForXcode`, registered only when `binaries.framework` exists. Xcode run script invokes the wrapper before Compile Sources, uses the IDE duplicate-build guard, disables dependency analysis for the phase, and requires User Script Sandboxing disabled. Custom Xcode configurations map `KOTLIN_FRAMEWORK_BUILD_TYPE` to Debug/Release.

Direct integration is local and unsuitable when the KMP project has CocoaPods dependencies. Preserve one chosen integration seam: direct, CocoaPods, or SwiftPM. CocoaPods plugin supplies XCFramework publication tasks; SwiftPM distribution requires its own artifact/checksum/version workflow.

## Consumer tests

Compile and run calls for:
- class/object/top-level/name mappings
- nullable/boxed primitives and collection/function conversions
- generic nullability
- `@Throws` expected/unexpected exceptions
- suspend completion/async cancellation/thread
- callbacks and object lifetimes
- imported native API and deployment availability
- static/dynamic framework embedding/signing

Snapshot generated `.h` and Swift interface plus symbol/artifact metadata. Kotlin compilation alone does not prove Swift source compatibility, linkability, minimum-OS launch, or ARC behavior.
