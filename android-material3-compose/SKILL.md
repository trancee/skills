---
name: android-material3-compose
description: "Designs, implements, reviews, tests, and migrates Android Material 3 interfaces with Jetpack Compose. Use when configuring Compose Material 3, themes, color schemes, typography, shapes, dynamic color, components, adaptive layouts, edge-to-edge UI, accessibility, motion, previews, UI tests, or Material 2 migration. Don't use for Android Views or XML, Wear OS Material 3, Compose Multiplatform shared UI, custom non-Material design systems, or state and business architecture unrelated to the interface."
compatibility: "Targets Android-only Jetpack Compose Material 3 apps. Current stable androidx.compose.material3 release is 1.4.0; prefer the current stable Compose BOM and verify adaptive artifacts separately. Dynamic color requires Android 12/API 31+. Edge-to-edge and predictive-back behavior depend on target/device SDK. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://m3.material.io/develop/android/jetpack-compose"
  sourceVersion: "Material Design 3 Android guidance; AndroidX Compose Material3 1.4.0 stable and 1.5.0-alpha27 (release notes updated 2026-08-26; inspected 2026-09-04)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-04T00:00:00+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-04T00:00:00+02:00"
---

# Android Material 3 Compose

## Step 1: Define the interface contract

1. DEFINE new app/screen | component | theme | adaptive layout | accessibility fix | Material 2 migration | visual regression | UI performance issue.
2. IDENTIFY target/compile/min SDK, Material3/Compose/Kotlin/AGP tuple, supported windows and postures, navigation pattern, content hierarchy, theme modes, dynamic-color policy, localization/RTL, accessibility behavior, state owner, experimental-API policy, and proof surface.
3. READ the current [Material Android Compose page](https://m3.material.io/develop/android/jetpack-compose), [Material3 release notes](https://developer.android.com/jetpack/androidx/releases/compose-material3), and affected component guidance before choosing APIs. Prefer the latest stable library; adopt alpha/beta only for a named requirement.
4. PRESERVE the product's existing design tokens, navigation/state contract, resource names, analytics semantics, and supported configurations unless the request changes them.
5. ROUTE shared Android/iOS/desktop/web UI to `compose-multiplatform`, Kotlin/Gradle failures to `kotlin-development` or `kotlin-gradle`, and BLE diagnostic interfaces to `android-ble-inspector`.

Completion: platform/version matrix, visual hierarchy, states, window classes, accessibility contract, and verification surfaces are explicit.

## Step 2: Inspect the Android project

RUN from the repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM app modules, Compose enablement/compiler plugin, Compose BOM and Material3/adaptive artifacts, Material 2 coexistence, theme definitions, dynamic color, edge-to-edge/insets, adaptive APIs, previews, semantic UI tests, and experimental opt-ins.

READ `references/setup-migration.md` before adding dependencies, upgrading Material3, or migrating Material 2.

Completion: the dependency owner, source owners, migration boundary, experimental APIs, and missing proof paths are known.

## Step 3: Establish one Material3 dependency and migration path

1. USE the existing version catalog and Compose BOM convention. Add only the Material3/adaptive artifacts required by the selected components.
2. ALIGN Kotlin, `org.jetbrains.kotlin.plugin.compose`, Compose BOM, AGP, compile SDK, and Material3 versions as a tested tuple. Never paste stale compiler-extension settings into a modern Kotlin 2.x build.
3. KEEP Material 2 and Material 3 side by side only during an explicit staged migration; never mix their `MaterialTheme`, component imports, or token types accidentally.
4. MIGRATE one coherent screen/theme boundary at a time, map M2 colors/typography/shapes to M3 roles, replace components intentionally, and delete obsolete M2 dependencies/imports at cutover.
5. OPT IN to experimental APIs at the narrowest file/declaration scope. Record the exact requirement, selected release, and migration risk; prefer stable alternatives.

Completion: each Compose module resolves one deliberate Material generation and no obsolete dependency or opt-in remains after clean cutover.

## Step 4: Build the theme and token system

READ `references/theme-motion.md`.

1. DEFINE light and dark `ColorScheme`, `Typography`, and `Shapes` once at the app theme boundary; consume them through `MaterialTheme` rather than screen-local constants.
2. USE matched container/on-container roles and semantic error/surface roles. Verify contrast instead of assuming generated or dynamic colors remain legible with custom overrides.
3. ENABLE dynamic color only on API 31+ behind a product setting or explicit policy; retain complete branded light/dark fallbacks and preview all paths.
4. KEEP typography scalable and language-safe: resource fonts, complete weights, deliberate line height, no clipped fixed-height text, and no text-bearing raster assets.
5. APPLY motion to express hierarchy, navigation, feedback, and continuity. Respect system animation scale and reduced-motion expectations; never delay completion or hide state behind animation.
6. USE Material 3 Expressive APIs only when present in the selected release and required by the product. Treat experimental expressive APIs as unstable, not as a wholesale visual refresh.

Completion: every component resolves color, type, shape, and motion from an intentional token with light/dark/dynamic and disabled/error coverage.

## Step 5: Compose components around observable states

READ `references/components-layout.md`.

1. SELECT the Material3 component whose semantics and interaction model match the action; customize slots/tokens before rebuilding a standard control from primitives.
2. MODEL loading, empty, content, selected, disabled, validation, error, destructive confirmation, and transient feedback where the use case can reach them.
3. HOIST screen state to its owner; keep composables rendering immutable state and emitting events. Key effects to their real lifecycle and keep I/O/navigation outside recomposition.
4. ACCEPT and honor a `Modifier` on reusable UI elements; apply it to the first emitted layout. Treat modifier order as behavior, especially padding, clipping, semantics, click targets, and insets.
5. USE lazy containers with stable keys for changing collections. Preserve selection, scroll, focus, and input across resize, rotation, navigation, and process recreation according to the contract.
6. USE `Scaffold` slots for coordinated bars/FAB/snackbar; apply its content padding exactly once and keep snackbar delivery owned outside the composable body.

Completion: controls expose the correct states/actions, recomposition causes no duplicate work, and state survives every named transition.

## Step 6: Make the whole window adaptive and edge-to-edge

1. CALL edge-to-edge setup at the Activity boundary and draw behind system bars. Apply `WindowInsets` or scaffold-provided padding at the content boundary; never combine equivalent inset consumers accidentally.
2. BASE layout decisions on current window size/posture, not device-name, orientation, or `isTablet` branches. Recompute while the app is running.
3. USE `NavigationSuiteScaffold` for top-level bar/rail adaptation when its policy matches; use canonical list-detail/supporting-pane/feed scaffolds for corresponding information architecture.
4. KEEP destination identity and pane/navigation history separate from visible arrangement so resizing never invents or loses navigation.
5. HANDLE IME, status/navigation bars, display cutouts, hinges, gesture regions, and predictive back. Verify compact, medium, expanded, large, and extra-large behavior where supported.
6. CONSTRAIN readable content width and use added space for hierarchy or parallel panes rather than stretching text and controls edge to edge.

Completion: runtime resize, fold/unfold, rotation, multi-window, IME, system bars, and back preserve content, focus, and navigation.

## Step 7: Make semantics, text, and interaction accessible

READ `references/accessibility-testing.md`.

1. PREFER Material3 controls' built-in semantics. Add role, label, state, error, heading, collection, progress, live-region, pane-title, or custom-action semantics only where the user-observable meaning is otherwise missing.
2. SET decorative icons to `contentDescription = null`; give icon-only actions a localized name through the control. Avoid duplicate child/parent announcements.
3. PROVIDE touch targets of at least 48 dp, visible focus, keyboard/D-pad traversal, meaningful order, and non-color cues for state.
4. VERIFY contrast, light/dark/high-contrast behavior, font scales through 200%, RTL, long translations, switch access, and TalkBack traversal/actions.
5. PRESERVE platform text selection, autofill, password, error, and input-method behavior; never replace mature text controls for appearance alone.

Completion: the interface remains understandable and operable without sight, color, touch, animation, English, or a compact phone window.

## Step 8: Preview, test, run, and report

1. ADD focused previews for important state × theme × locale × font-scale × window combinations. Keep previews deterministic and side-effect-free; never treat them as runtime proof.
2. ADD Compose semantics tests only for durable user-observable behavior: state transitions, selection, validation/error, navigation, restoration, and custom semantics. Use `arrange-act-assert` for example-based test structure.
3. USE screenshot/golden tests only when pixels or token rendering are an explicit contract; stabilize fonts, density, locale, clock, animations, and device configuration.
4. RUN the affected Gradle build/test tasks, then launch the actual Activity on an emulator or device. Exercise edge-to-edge, input, back, resize/rotation, light/dark/dynamic color, large text, RTL, and accessibility service behavior relevant to the change.
5. PROFILE measured jank/recomposition issues with release-like builds before optimizing; never infer runtime performance from recomposition counts alone.
6. COPY `assets/material3-compose-report.md`; record versions, theme policy, components/states, adaptive/inset behavior, accessibility, experimental APIs, automated checks, runtime matrix, and limitations.

Completion: deterministic checks prove behavior and an actual Android surface proves rendering, interaction, system integration, and accessibility.

## Error Handling

- Material3 symbols remain unresolved -> verify Google Maven, module Compose enablement, version-catalog alias, BOM mapping, and artifact coordinate before changing imports.
- Compiler/plugin errors follow an upgrade -> align Kotlin and `org.jetbrains.kotlin.plugin.compose`; remove stale `kotlinCompilerExtensionVersion` configuration where the current toolchain no longer uses it.
- Colors look wrong in dark/dynamic mode -> remove hard-coded foreground/background pairs and use matched `ColorScheme` roles; verify contrast on every scheme.
- Content overlaps bars or receives double padding -> trace inset ownership from Activity through Scaffold to leaf; consume each inset once.
- Layout fails on tablet/foldable -> branch from available window size/posture and adapt continuously; remove device/orientation assumptions.
- Back exits the wrong pane -> define destination history and adaptive pane back behavior explicitly; never derive history from current width.
- TalkBack repeats or omits a control -> inspect merged/unmerged semantics; rely on Material semantics and add only missing user meaning.
- UI test flakes -> remove sleeps, external data, live animation, and unstable node lookup; synchronize through Compose idleness/test clock and observable semantics.
- Expressive API disappears -> return to stable Material3 APIs or pin the explicitly approved prerelease; do not hide breakage behind broad suppressions.

## Official references

- Material Android Compose: https://m3.material.io/develop/android/jetpack-compose
- Material3 in Compose: https://developer.android.com/develop/ui/compose/designsystems/material3
- Material3 releases: https://developer.android.com/jetpack/androidx/releases/compose-material3
- Material 2 migration: https://developer.android.com/develop/ui/compose/designsystems/material2-material3
- Adaptive Compose: https://developer.android.com/develop/ui/compose/layouts/adaptive
- Accessibility: https://developer.android.com/develop/ui/compose/accessibility
- Compose testing: https://developer.android.com/develop/ui/compose/testing
