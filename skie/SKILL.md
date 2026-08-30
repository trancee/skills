---
name: skie
description: "Installs, migrates, configures, and troubleshoots Touchlab SKIE for Kotlin Multiplatform Swift interop. Use when adding co.touchlab.skie to an Apple framework module, exposing Kotlin Flow, suspend functions, enums, sealed types, or default arguments to Swift, tuning SKIE features or analytics, or fixing SKIE build and migration failures. Don't use for general Kotlin or Swift work without SKIE, non-Apple KMP targets, or Swift-only projects."
compatibility: "Requires a Gradle Kotlin Multiplatform module producing Apple frameworks. Framework/Swift verification requires macOS, Xcode, and a supported Kotlin/Swift/SKIE combination. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://skie.touchlab.co/intro"
  sourceVersion: "SKIE 0.10.14 (touchlab/SKIE@2fdb1a3937530540e6c850a2a8362d41f20da77a)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T13:07:08+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T13:07:08+02:00"
---

# SKIE

## 1. Scope+refresh

1. DEFINE new install | existing migration | config | interop API | build/runtime failure.
2. IDENTIFY framework-producing KMP module, Apple targets, framework/XCFramework path, Swift consumer, Kotlin/Swift/Xcode/SKIE versions, distribution method.
3. READ current [intro](https://skie.touchlab.co/intro), [Installation](https://skie.touchlab.co/Installation), relevant [changelog](https://skie.touchlab.co/category/changelog), and feature page before version/config edits. Metadata version=authoring snapshot only.
4. Existing project -> READ [migration](https://skie.touchlab.co/migration) + `references/migration-troubleshooting.md` before plugin application.

## 2. Inspect

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```
CONFIRM: KMP module; `framework`/CocoaPods signal; plugin application location/version; Kotlin version; annotations version; repositories; SKIE config; Swift source/tests.

Plugin must apply only to modules producing Xcode frameworks. Exported dependencies are also transformed.

## 3. Establish baseline

Existing project:
1. BUILD current framework/XCFramework with wrapper.
2. COMPILE+test Swift consumer.
3. SNAPSHOT exported Swift API or compile diagnostics; inventory manual Flow/async wrappers, enum/sealed switches, casts, renamed calls.
4. SELECT incremental feature scope. Avoid all-at-once migration for large/multi-team consumers.

New project: keep SKIE defaults unless a verified requirement differs.

## 4. Install

1. Add current plugin in framework module only:
   ```kotlin
   plugins {
       id("co.touchlab.skie") version "<SKIE_VERSION>"
   }
   ```
2. If unresolved, ensure `pluginManagement.repositories` includes `mavenCentral()`; preserve existing `google()`/`gradlePluginPortal()` policy.
3. RUN wrapper framework link task. Never add undocumented runtime dependencies; plugin manages generated/runtime artifacts.
4. Version gate: current docs authoring snapshot supports Kotlin 2.0.0..2.4.10 and Swift >=5.8/Xcode>=14.3. Re-read live intro/changelog; SKIE rejects unsupported Kotlin.

## 5. Configure

READ `references/install-config.md`.

- global Gradle rules establish defaults; `group("fq.name.prefix")` matches prefixes; last matching value wins
- annotations override Gradle rules unless matching group uses `overridesAnnotations=true`
- dependency/external declarations require Gradle rules; owned source may use annotations
- annotations require `co.touchlab.skie:configuration-annotations:<SKIE_VERSION>` in relevant source set
- existing migration: disable broad feature, then enable narrow packages/declarations
- analytics choice explicit: default upload, `disableUpload`, or `enabled=false`
- distributable binary framework -> `skie.build.produceDistributableFramework()`

## 6. Migrate Swift API

READ `references/interop.md` for selected features.

- enums: generated Swift enum; original Kotlin enum=`__Type`; fix case names/default switches/generic/interface boundaries
- sealed: use `onEnum(of:)`; handle `.else` for hidden children
- suspend: generated Swift `async`; two-way cancellation; generic receiver=`skie(value)`; override original `__method`; audit thread assumptions
- Flow: generated `AsyncSequence`; remove manual bridges/casts; test cancellation; follow unsupported-conversion rules
- global/interface extensions/overloads: update generated Swift call names
- default arguments: disabled by default; deprecated implementation; enable only selected declarations after size/cache review

Treat generated Swift API and compiler diagnostics as source truth. Do not guess generated names.

## 7. Verify

1. RUN affected framework link task; then all Apple framework/XCFramework tasks changed by shared config.
2. Inspect produced framework Swift interface/generated Swift.
3. Compile+test actual Swift consumer.
4. Test selected boundaries:
   - enum/sealed exhaustive switches and conversions
   - suspend result/error/cancel/background-thread behavior
   - Flow elements/generic types/cancel/error/conversion limitations
   - exported dependency and cinterop declarations
   - static/dynamic/distributable framework import on intended machine
5. Compare API snapshot/binary distribution expectations. No macOS/Xcode => report config inspection only; Apple build+Swift use unverified.

## 8. Diagnose+report

READ `references/migration-troubleshooting.md`. Fix first failing boundary: plugin resolution -> Kotlin compatibility -> framework link -> Swift compile -> runtime semantics.

OUT: copy `assets/integration-report.md`; record exact versions/module/tasks/artifacts/config/features/API changes/Swift tests/limits. Remove disposable artifacts.

## Fail

- no Apple framework-producing module => SKIE not applicable
- unsupported Kotlin/SKIE/Swift => select documented compatible versions; no check bypass
- cached artifact 404/ClassNotFound => `./gradlew <task> --refresh-dependencies`; persistent regional cache => wait/retry, then upstream issue
- existing Swift source breaks => staged feature migration, not Kotlin rewrite
- custom cinterop unknown framework => configure exact framework name or use original Kotlin declaration
- host cannot link Apple framework => finish static inspection; mark runtime/Swift proof unavailable
