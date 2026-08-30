# Kotlin Multiplatform

## Source set

Choose narrowest set covering intended targets:
- `commonMain/commonTest`: all targets
- platform set (`jvmMain`,`jsMain`,`linuxX64Main`): one target APIs/deps
- intermediate (`appleMain`): target subset

Child can see parent; common cannot see platform API/dep. READ [project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html) before moves.
Platform top-level file suffix: `Platform.jvm.kt`; common: `Platform.kt`; prevents duplicate JVM facade.

## Targets/deps

Declare every output target in `kotlin {}`. Parent source change => compile every attached target.
iOS device/simulator distinct targets; shared code normally `iosMain`; leaf sets only differences.
Dependency belongs to narrowest using source set; `commonMain` dependency must publish every target variant.

## Platform bridge

Prefer common interface + injected platform implementations. Use `expect/actual` only when common code names platform declaration.
1. `expect` no body in common/intermediate
2. matching `actual` in every leaf or suitable intermediate
3. same package/kind/name/compatible signature
4. compile all actualizing targets

Prefer function/property/interface/factory over expected class. Expected classes Beta+opt-in. READ [expect/actual](https://kotlinlang.org/docs/multiplatform/multiplatform-expect-actual.html).

## Tests

Shared contract=`commonTest`+`kotlin.test`; platform behavior=matching test set; run discovered `<targetName>Test`. Host-limited target explicit unverified. JVM PASS != other target PASS.
