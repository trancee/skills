# SKIE migration/troubleshooting

## Existing project sequence

1. Baseline Kotlin framework link + Swift compile/tests/API.
2. Read selected feature docs and breaking changes.
3. Apply plugin only to framework module.
4. For large consumer, disable broad feature(s); enable one package/declaration at a time.
5. Rebuild framework; inspect generated Swift; fix Swift compile errors; run runtime tests.
6. Remove obsolete manual Kotlin-Swift wrappers only after equivalent SKIE behavior passes.

Kotlin source normally remains valid; migration changes Swift source/API and runtime cancellation/thread semantics.

## First-failure map

| symptom | action |
|---|---|
| plugin not found | add `mavenCentral()` to plugin repositories |
| artifact 404 or wrong JAR/`ClassNotFoundException` after release | `./gradlew <linkTask> --refresh-dependencies`; wait for regional cache; retry; issue if >1 day |
| unsupported Kotlin | read intro/changelog; align Kotlin+SKIE; never bypass check |
| Foundation symbol missing in Swift | add explicit `import Foundation` beside Kotlin framework import |
| `__SkieUnknownCInteropFrameworkErrorType` | configure `ClassInterop.CInteropFrameworkName("Framework")` for FQ prefix, or call original Kotlin declaration |
| `__SkieLambdaErrorType` | lambda nested as generic type unsupported; redesign exposed signature or use original callable |
| enum member/default switch errors | inspect generated case names; remove unreachable `default`; convert `__Enum`/Swift enum where boundary requires |
| suspend generic member missing | call `skie(instance).method()` |
| Swift suspend override missing | override `__method`; test lost nested cancellation bridge |
| Flow cast crash/`Expected ... found Kotlin_kobjcc0` | use SKIE conversion constructors; no ordinary transformed-wrapper casts |
| Flow custom exception crash | prevent custom exception crossing Flow bridge or redesign error representation |
| framework works locally, fails on another machine | enable `produceDistributableFramework()` and rebuild artifact |

## Runtime regression checks

- Swift task cancellation cancels Kotlin suspend/Flow work.
- Kotlin cancellation maps as documented; Flow cancellation ends sequence without error.
- Code with prior main-thread assumption explicitly enters correct actor/dispatcher.
- Flow generic/nullable wrapper type matches generated interface.
- Exported dependency behavior matches intended Gradle prefix rules.
- Analytics policy matches organization requirement.

Known issues index: [current limitations](https://skie.touchlab.co/category/known-issues-and-limitations).
