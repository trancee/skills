---
name: compose-multiplatform
description: "Designs, implements, tests, and ships shared Compose Multiplatform UI. Use when configuring Compose and compiler plugins; choosing Android, iOS, desktop, JS, or Wasm UI sharing; structuring common composables and platform entry points; managing state, lifecycle, ViewModel, navigation, resources, localization, accessibility, previews, or native-view interop; testing UI semantics; packaging apps; and diagnosing recomposition or platform-specific behavior. Don't use for non-Compose Kotlin Multiplatform architecture, Android Views or XML-only UI, SwiftUI-only apps, raw Skia rendering, or Gradle and toolchain work unrelated to Compose."
compatibility: "Current Compose Multiplatform 1.12.0 supports Android 5/API 21, iOS 14, macOS 13 arm64, Windows 10 x86-64/arm64, Ubuntu 20.04 x86-64/arm64, and WasmGC browsers. Use Kotlin 2.1+; prefer 2.2.20+ for iOS/web. Compose compiler plugin version must equal Kotlin/KMP plugin version. Desktop runtime requires JDK 11+ and native packaging JDK 17+. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/multiplatform/compose-multiplatform.html"
  sourceVersion: "Compose Multiplatform 1.12.0; Kotlin 2.4.10; Kotlin Multiplatform Help build 554 (2026-08-26)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T18:15:26+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T09:38:56+02:00"
---

# Compose Multiplatform

## Step 1: Define the shared UI contract

1. DEFINE new app/screen | target addition | shared UI migration | state/recomposition | resources/localization | lifecycle/ViewModel | navigation | native interop | accessibility | UI test | preview/hot reload | packaging | platform bug.
2. IDENTIFY products/modules, Android/iOS/desktop/JS/Wasm targets, minimum OS/browser/JDK, shared versus native UI, platform entry points, window/safe-area/input behavior, state owner, navigation owner, resources, accessibility contract, host matrix, and distribution artifacts.
3. READ the current [Compose Multiplatform overview](https://kotlinlang.org/docs/multiplatform/compose-multiplatform.html), [compatibility table](https://kotlinlang.org/docs/multiplatform/compose-compatibility-and-versioning.html), and destination release notes before setup or upgrade.
4. PRESERVE existing module/source-set boundaries, design system, state/event contract, navigation routes, resource IDs, platform shells, and distribution identifiers unless the request changes them.
5. ROUTE Android BLE inspector/diagnostic surfaces to `android-ble-inspector`, generic KMP targets/hierarchy/publication to `kotlin-multiplatform`, compiler/toolchain/cache mechanics to `kotlin-gradle`, Kotlin behavior to `kotlin-development`, and Swift framework/device deployment to `kotlin-native-apple-interop`/`xtool`.

Completion: target/host matrix, shared UI boundary, platform shells, state/navigation ownership, accessibility behavior, and proof surfaces are explicit.

## Step 2: Inspect the project and version tuple

RUN from the target repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM KMP/Compose/compiler plugin versions and owners, targets/environments, source sets, Compose dependencies, resources, composables, platform entry points, state/effect APIs, ViewModel/lifecycle/navigation, UI tests, previews, interop, desktop packaging, web compatibility, and platform imports in common code.

READ `references/setup-targets.md`. APPLY `org.jetbrains.compose` and `org.jetbrains.kotlin.plugin.compose` to every Compose module; align the compiler plugin exactly with Kotlin/KMP, version Compose Multiplatform independently, and use the release table's direct dependency coordinates.

Completion: every Compose module has a compatible plugin/dependency tuple, and every executable app target has a platform entry point.

## Step 3: Structure modules, targets, and entry points

1. KEEP reusable screen/design-system UI in the narrowest common/intermediate source set supported by its APIs.
2. KEEP platform app shells and entry points platform-owned: Android activity, iOS controller/app, desktop `main`/window, and JS/Wasm page attachment.
3. PLACE platform APIs, permissions, native SDK integrations, system UI, and UX divergences in platform source sets behind common interfaces/callbacks.
4. SHARE UI only where behavior should remain shared; a shared ViewModel/data layer with native UI is a valid boundary.
5. DECLARE only shipped/tested targets and use their real host tools; iOS build/run requires macOS and Xcode.

Completion: each source file and dependency sits in the narrowest source set serving its UI consumers.

## Step 4: Implement composables, state, and effects

READ `references/state-effects.md`.

1. MODEL immutable UI state and explicit user events; hoist state to the lowest common owner that needs to read/write it.
2. KEEP composables referentially transparent: render state and emit events; move I/O, navigation decisions, and business mutation to owned state/effect layers.
3. USE `remember` for composition-lifetime state, `rememberSaveable` with a valid saver for restorable UI state, and ViewModel/repository state for durable flows.
4. USE `LaunchedEffect`, `DisposableEffect`, `SideEffect`, `produceState`, or `rememberCoroutineScope` only for their documented lifecycle; choose keys from the values whose change requires restart/disposal.
5. KEEP parameters stable/immutable where measured recomposition matters; optimize only from profiler/compiler/runtime evidence.

Completion: state has one owner, effect lifecycle is keyed, and recomposition produces no duplicate work or lost user state.

## Step 5: Add resources, layout, input, and accessibility

READ `references/resources-accessibility.md`.

1. STORE shared assets under `<sourceSet>/composeResources` with required default resources and generated `Res` accessors.
2. USE qualifiers for locale/theme/density and test fallback/RTL/large text. Load large raw/system-consumed files through URIs rather than synchronously buffering them in composition.
3. DESIGN adaptive layouts from window constraints/insets, not platform-name branching; handle keyboard/safe-area, mouse/touch/keyboard, focus, back, and scroll differences explicitly.
4. PROVIDE semantic role, label/content description, state, action, traversal, and focus behavior for custom controls; preserve semantics through native interop.
5. VERIFY real text/font rendering per platform; cross-platform screenshot pixels are not inherently identical.

Completion: resources resolve on every target and the UI remains operable with target input methods and assistive technologies.

## Step 6: Add lifecycle, ViewModel, and navigation

READ `references/lifecycle-navigation.md`.

1. DEPEND on `org.jetbrains.androidx` multiplatform lifecycle/navigation artifacts in common code at versions compatible with the Compose release.
2. COLLECT observable state with lifecycle-aware APIs where lifecycle exists; account for web lifecycle omissions and desktop/iOS mappings.
3. CREATE common ViewModels with an explicit initializer/factory because non-JVM targets lack reflective no-arg construction.
4. ADD `kotlinx-coroutines-swing` for desktop lifecycle/ViewModel `Dispatchers.Main.immediate` use.
5. DEFINE serializable typed routes, pass stable IDs/minimal arguments, load complex state from its owner, and scope ViewModels/saveable state explicitly to destinations when the navigation API requires it.
6. REGISTER deep links and back behavior in each platform shell; test native gesture/keyboard differences.

Completion: lifecycle transitions, destination scope, back stack, restoration, and deep links have platform-specific evidence.

## Step 7: Integrate native views and platform UX

READ `references/platform-interop.md`.

1. CHOOSE the seam: Compose screen inside native shell, native view inside Compose, or fully native screen over shared state.
2. CREATE native objects in `factory`/entry-point construction, update only changed properties in `update`, and release delegates/listeners/sessions at disposal.
3. KEEP callbacks stable and thread UI mutations on the platform UI thread; prevent feedback loops between native and Compose state.
4. DEFINE size, clipping, z-order, accessibility, focus, touch arbitration, lifecycle, and ownership at every interop boundary.
5. VERIFY actual platform UX; Android/iOS/desktop/web defaults intentionally differ.

Completion: native and Compose ownership/disposal are single-valued and interaction works on the real target.

## Step 8: Test shared and platform UI

READ `references/testing.md`.

1. PUT shared semantics/state-transition tests in `commonTest` using `runComposeUiTest`; use finders/actions/assertions on user-observable semantics.
2. PUT rendering, interop, lifecycle, input, accessibility, and distribution tests in the owning platform test source set/runner.
3. CONTROL clocks/idleness and inject deterministic state; never synchronize with sleeps.
4. TEST empty/loading/error/content, restoration, locale/RTL/theme/density/large text, keyboard/focus/back, deep links, and platform-specific branches.
5. RUN each affected target. A desktop pass does not verify iOS touch, Android instrumentation, or Wasm browser behavior.

Completion: every changed shared contract and platform divergence has deterministic behavioral evidence.

## Step 9: Run, package, migrate, and report

READ `references/packaging-migration.md`.

1. RUN the actual Android/iOS/desktop/web surface; use JVM-only Hot Reload/previews for iteration, never final cross-platform proof.
2. BUILD release artifacts with target packaging/signing/minification/resources and smoke-install/serve them.
3. FOR web compatibility, build both JS and Wasm through `composeCompatibilityBrowserDistribution` when older-browser fallback is required.
4. MIGRATE Compose, Kotlin/compiler plugin, lifecycle/navigation/resources, and deprecated APIs as one tested compatibility tuple; delete stale compiler coordinates/options.
5. COPY `assets/compose-report.md`; fill versions, targets, shared boundary, state/effects, resources, navigation, accessibility, tests, packaging, and limitations.

Completion: real target surfaces and release artifacts satisfy the UI contract, with unavailable hosts explicitly unverified.

## Error Handling

- Compose compiler/plugin mismatch -> set `org.jetbrains.kotlin.plugin.compose` to the exact Kotlin/KMP version in every Compose module.
- Compose APIs unresolved in common code -> use `org.jetbrains.compose`/supported multiplatform artifacts in the correct source set; move platform-only APIs down.
- Missing `Res` accessor/resource -> verify resources dependency, `composeResources` directory/type/qualifier, generated package, and clean stale build outputs after version migration.
- Duplicate I/O/navigation/relaunch on recomposition -> move work into the correct keyed effect or state owner; do not guard with ad hoc Boolean globals.
- Desktop ViewModel/lifecycle dispatcher failure -> add compatible `kotlinx-coroutines-swing` and verify main-dispatcher initialization.
- UI test hangs -> inspect pending composition/measure/layout, test clock, unbounded animation, and dispatcher ownership; replace sleeps with idleness/clock control.
- iOS/web/desktop behavior differs -> check documented platform defaults and test on the target before adding a platform branch.
- Native interop leak/crash -> make factory/update/disposal ownership explicit and release delegates/listeners/native sessions.
- Desktop package task fails -> use JDK 17+ and verify target formats/modules/resources; runtime-only success is insufficient.
- iOS task unavailable -> move build/run evidence to macOS/Xcode; do not mark the target verified from common compilation.
