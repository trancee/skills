# Setup and Material 2 migration

## Version decision

1. READ the current Material3 release notes and Compose BOM mapping before editing dependencies.
2. PREFER the latest stable Material3 release. Select alpha/beta only when a named component or bug fix is unavailable in stable and the project accepts source/API churn.
3. KEEP Kotlin, the Kotlin Compose compiler plugin, AGP, compile SDK, Compose BOM, Material3, adaptive libraries, Lifecycle, Activity Compose, and Navigation in a recorded compatibility tuple.
4. FOLLOW the repository's version catalog/BOM style. Do not introduce direct versions beside a catalog or BOM owner.

As inspected on 2026-09-04, `androidx.compose.material3:material3` stable is 1.4.0 and 1.5.0-alpha27 is prerelease. Re-check rather than copying these values.

## Modern dependency shape

Prefer the existing catalog aliases. A direct Kotlin DSL shape is:

```kotlin
dependencies {
    implementation(platform("androidx.compose:compose-bom:<current-stable-bom>"))
    androidTestImplementation(platform("androidx.compose:compose-bom:<same-bom>"))

    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:<compatible-version>")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:<compatible-version>")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
```

Add only when required:

- `androidx.compose.material3:material3-adaptive-navigation-suite` for adaptive top-level navigation.
- `androidx.compose.material3.adaptive:adaptive`, `adaptive-layout`, and `adaptive-navigation` for adaptive info and pane scaffolds.
- `androidx.compose.material:material-icons-extended` only when its size/startup tradeoff is accepted; prefer app-owned vector resources for a small icon set.

Verify whether the selected BOM manages each adaptive artifact. If it does not, declare one compatible explicit version in the catalog.

For Kotlin 2.x projects, apply `org.jetbrains.kotlin.plugin.compose` at the same version as Kotlin according to the Kotlin/Compose compiler guidance. Never add a historical `composeOptions.kotlinCompilerExtensionVersion` merely because an old sample contains it.

## Project inspection

Confirm all of these before implementation:

- Compose enabled in every UI module.
- One version owner for every Compose coordinate.
- Google Maven available.
- Minimum/target/compile SDK and Java/Kotlin toolchain compatible with dependencies.
- `androidx.compose.material3` imports use Material3 theme/components consistently.
- `androidx.compose.material` imports are either intentionally staged or removed.
- UI tooling is debug-only; test artifacts use test configurations.
- Experimental opt-ins name the exact API family and remain narrow.

## Material 2 to Material 3 cutover

Material 2 and Material 3 types are distinct even when names match. Migrate deliberately:

| Material 2 | Material 3 decision |
| --- | --- |
| `androidx.compose.material.MaterialTheme` | `androidx.compose.material3.MaterialTheme` |
| `Colors` / `lightColors` / `darkColors` | `ColorScheme` / `lightColorScheme` / `darkColorScheme` |
| `primaryVariant`, `secondaryVariant` | Map by semantic role; do not mechanically rename |
| `Typography` names such as `h1`, `subtitle1`, `body1` | Map to display/headline/title/body/label scale by intended hierarchy |
| M2 component import | Select the corresponding M3 component and review changed defaults/slots/state |
| elevation overlay | Use M3 surface roles and tonal elevation deliberately |

Procedure:

1. Freeze the screen's observable states, actions, navigation, accessibility labels, and visual reference.
2. Introduce the M3 theme at one coherent subtree or screen boundary.
3. Map brand colors to M3 semantic roles using Material Theme Builder or an owned token mapping; provide complete light and dark schemes.
4. Map typography and shapes by hierarchy and use, not old property names.
5. Replace components and review parameter/default differences, minimum sizes, insets, and semantics.
6. Verify light/dark, dynamic color policy, large text, RTL, edge-to-edge, and interaction states.
7. Move the next boundary only after the prior one runs correctly.
8. Delete M2 imports, theme code, dependencies, adapters, and temporary aliases once no caller remains.

Never keep parallel app themes, copied color constants, or wrapper aliases after the clean cutover.

## Experimental APIs

Use a prerelease or experimental API only when:

- The requirement names behavior unavailable in stable.
- Release notes confirm the API exists in the selected version.
- The opt-in is scoped to the smallest declaration/file.
- A stable fallback or upgrade responsibility is recorded.
- UI tests/runtime checks cover the unstable behavior.

Material 3 Expressive is an expansion of M3, not a requirement to replace every component. Some expressive APIs graduate independently. Check annotations and release notes for the exact selected version.
