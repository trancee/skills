---
name: kotlin-development
description: "Implements/reviews/builds/tests/debugs Kotlin across JVM, Android, Multiplatform, JS, Wasm, Native. Use for Kotlin source, Gradle/Maven, toolchain alignment, coroutines, Java interop, compiler/test failures. Don't use for Java-only, non-Kotlin Android UI, or unrelated build work."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/home.html"
  sourceVersion: "Kotlin 2.4.10; Kotlin Help build 1155; Kotlin Multiplatform Help build 554"
  sourceBuiltAt: "2026-08-26"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T10:56:53+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# Kotlin development

## 1. Scope+inspect

1. DEFINE change: source | build | test | Java interop | coroutine | KMP source set.
2. RECORD affected modules, targets, public API, runtime, minimum Kotlin/Java/Gradle/Maven/AGP/native toolchain.
3. PRESERVE current build/Kotlin/language/API/plugin/style/test versions unless migration requested.
4. Version/new API => READ current [docs](https://kotlinlang.org/docs/home.html)+[releases](https://kotlinlang.org/docs/releases.html).
5. RUN from target root:
   ```bash
   python3 scripts/inspect-project.py --root . --json
   ```
6. VERIFY detected build, wrapper, files, plugins, source sets, targets, Kotlin count.
7. JIT READ:
   - build/deps/toolchain/version -> `references/build-tools.md`
   - KMP plugin/source sets/multi-target -> `references/multiplatform.md`
   - null/Java/coroutine/public API/style -> `references/language-safety.md`
   - tests -> `references/testing.md`

## 2. Establish behavior

- bug: narrowest module+target reproduction; user-supplied exact failure=established
- feature: observable contract + owning test layer
- trace diagnostic to first boundary: platform nullability | source-set visibility | cancellation | JVM target | dependency
- classify source vs build/JDK/daemon/IDE/SDK/Xcode/Node/browser/linker before Kotlin edit

## 3. Change

- code -> narrowest source set serving all callers; no platform API in `commonMain`
- nullability stays typed; unsafe `!!` -> check/safe call/Elvis/explicit boundary failure unless local invariant proven
- Java platform type contained at interop boundary; explicit Kotlin type or owned-Java annotation
- coroutine -> owned `CoroutineScope`; parent-child cancellation; rethrow `CancellationException`; await relevant result
- style -> repo formatter/rules, else [Kotlin conventions](https://kotlinlang.org/docs/coding-conventions.html)
- published API -> preserve source+binary compatibility OR state break before edit

## 4. Build config iff required

- use checked-in Gradle/Maven wrapper
- compatibility: KGP+Gradle+AGP+JDK+language+API+JVM target; read live table
- Gradle: typed `compilerOptions {}`; broad extension defaults; target/task overrides only differences
- align Kotlin/Java target via toolchain/matching targets; never disable validation
- dependency -> owning module/source set; preserve catalog/management/repository policy
- migration separable from behavior fix => separate change

## 5. Tests+proof

1. Add test only for uncovered observable contract; prove red on bug/gap.
2. KMP shared -> `commonTest`; platform behavior -> matching test source set.
3. Coroutine contracts: completion,cancel,propagation,virtual time.
4. Java boundary: nullable platform values, mutability, checked errors, JVM names as relevant.
5. Discover tasks; run narrow compile/test per changed target, then owning module full test.
6. Run configured format/lint/static/API/package checks.
7. Shared KMP change => compile every affected target; host-incompatible target=explicit unverified.
8. Exercise runtime path; compile alone insufficient for coroutine/interop/serialization/UI/native behavior.
9. OUT: copy `assets/completion-report.md` iff durable report needed; exact commands/results/artifacts/warnings/limits; remove disposable output.

## Fail

- inspector=mixed Gradle+Maven => identify owner; no dual update
- no wrapper => repo bootstrap; ask before generate/upgrade
- incompatible versions => smallest boundary from live table
- JVM target mismatch => align with existing toolchain policy
- platform API in `commonMain` => platform source set OR common interface+implementations
- coroutine test hangs => inspect owner/await/cancellation/dispatcher; no larger timeout workaround
- host lacks target => finish reachable compile/tests; mark target unverified
