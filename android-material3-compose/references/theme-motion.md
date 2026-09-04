# Theme, tokens, and motion

## Theme boundary

Create one app-owned theme composable that chooses the scheme and supplies all Material subsystems:

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && darkTheme ->
            dynamicDarkColorScheme(context)
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            dynamicLightColorScheme(context)
        darkTheme -> AppDarkColorScheme
        else -> AppLightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content,
    )
}
```

Keep system-bar icon appearance coordinated with the actual background, but do not mutate system UI from every recomposition. Prefer current edge-to-edge APIs over obsolete accompanist/system-ui-controller recipes.

## Color

Use semantic role pairs:

- `primary` / `onPrimary` and `primaryContainer` / `onPrimaryContainer` for the strongest branded actions and selected emphasis.
- `secondary` and `tertiary` families for supporting emphasis, not arbitrary decoration.
- `surface`, `surfaceContainer*`, and corresponding `onSurface*` roles for layered content.
- `error` / `onError` and `errorContainer` / `onErrorContainer` for failures.
- `outline` / `outlineVariant` for boundaries that must remain visible.

Rules:

1. Pair an `on*` role only with its matching base/container unless contrast is measured.
2. Avoid raw `Color(...)` values in screens and components. Keep owned palette values in theme/token files.
3. Never communicate state through color alone; add icon, text, shape, or semantics.
4. Verify generated, custom, and dynamic schemes independently. Dynamic color can change brand emphasis and contrast around custom assets.
5. Use tonal elevation and surface container roles intentionally. Do not simulate elevation with arbitrary translucent overlays.
6. Test disabled, focused, pressed, hovered, selected, dragged, error, and high-contrast states.

Material Theme Builder can generate Compose light/dark schemes from source colors. Treat generated files as source to normalize into project naming/ownership, not as a second design system.

## Typography

Material3 groups styles as display, headline, title, body, and label, each with large/medium/small variants.

- Assign styles by content hierarchy and function, not desired pixel size.
- Package font resources and all required weights; verify synthetic weight is acceptable if a weight is absent.
- Keep body copy readable and constrain long-form line length rather than stretching it across expanded windows.
- Let text reflow at 200% font scale. Avoid fixed heights and baseline assumptions that clip diacritics or scripts.
- Use `sp`, localized strings, plural resources, and locale-aware number/date formatting.
- Verify fallback glyphs, bidirectional text, and line breaking with representative locales.

## Shapes and component tokens

Define `Shapes` once, then use component defaults and token overrides. Shape communicates grouping, prominence, and transition; random corner radii create hierarchy noise.

Customize through the narrowest supported surface:

1. Component parameters/default factories for one component instance or family.
2. `MaterialTheme` color/typography/shapes for app-wide Material behavior.
3. App semantic tokens layered over `MaterialTheme` only when the product has stable roles Material does not express.
4. Custom drawing only when Material/component APIs cannot satisfy the contract.

## Motion

Use motion for:

- Spatial continuity between navigation destinations or adaptive panes.
- State change, selection, expansion, loading, or success/error feedback.
- Hierarchy through duration, easing, and container transformation.

Never:

- Start effects directly in a composable body.
- Use animation as the sole state indicator.
- Block input or completion for decorative motion.
- run infinite decorative animation when the UI is not visible.
- Assume one duration/easing remains appropriate under disabled or reduced system animation.

Use `animate*AsState` for one value, `updateTransition` for coordinated state, `AnimatedVisibility` for enter/exit, and navigation/shared-transition APIs only when lifecycle and identity are explicit. Drive animations from state, use stable keys, and test with the Compose clock.

## Material 3 Expressive

Adopt expressive theming/components/motion selectively:

1. Confirm the product requirement and the exact API in release notes.
2. Prefer stable APIs in the selected stable Material3 release.
3. Scope `ExperimentalMaterial3ExpressiveApi` or other opt-ins narrowly when unavoidable.
4. Verify component size, shape morphing, motion, contrast, semantics, and back/adaptive behavior.
5. Record a migration owner because alpha APIs can rename, change defaults, or disappear.

Wear OS uses Wear Compose Material 3, not the Android phone/tablet Material3 library covered here.
