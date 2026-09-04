# Components, layout, and adaptive behavior

## Select by meaning

| Need | Prefer | Avoid |
| --- | --- | --- |
| Primary textual action | `Button` / suitable tonal, elevated, outlined variant | Clickable `Box` styled like a button |
| Icon-only action | `IconButton` with localized action name | Bare clickable `Icon` |
| Prominent primary screen action | `FloatingActionButton` when Material guidance fits | FAB for every frequent action |
| Immediate binary setting | `Switch` in a labeled row | Checkbox with ambiguous side effect |
| Independent multi-selection | `Checkbox` | Radio buttons |
| Exactly one choice | `RadioButton` with selectable parent row | Independent switches |
| Text entry | `TextField` / `OutlinedTextField` | Custom basic field without full input semantics |
| Temporary action feedback | `Snackbar` through one `SnackbarHostState` owner | Toast-like overlay emitted during recomposition |
| Blocking decision | `AlertDialog` with explicit actions | Modal dialog for passive information |
| Contextual options | Dropdown/menu | Permanent action row that crowds content |
| Large collection | `LazyColumn` / `LazyGrid` with stable keys | Eager column of unbounded items |
| App structure | `Scaffold` and navigation components | Manually overlaid bars/FAB/content |

Make the entire labeled row interactive for check/radio/switch patterns when appropriate, then merge semantics deliberately. Keep destructive actions visually and semantically distinct and confirm only when the consequence warrants interruption.

## Component state contract

For each component or screen, enumerate reachable states before styling:

- Loading, empty, content, stale/refreshing, and recoverable/fatal error.
- Enabled, disabled with reason, focused, pressed, hovered, selected, and dragged.
- Valid/invalid input, supporting/error text, password visibility, IME action, and submit progress.
- Dialog/sheet/menu closed/open/dismissing and restoration after process recreation where required.
- Snackbar queued/current/dismissed/actioned without replay after rotation.

Expose state and callbacks. Keep I/O and navigation in an owner outside reusable UI. Do not duplicate owner state with `remember` merely to animate it; use derived or transition state.

## Modifier contract

Reusable elements accept `modifier: Modifier = Modifier` as the first optional parameter and apply it once to the first emitted UI node. Do not reuse one modifier across multiple siblings.

Order changes behavior:

```kotlin
Modifier
    .clickable(onClick = onClick) // includes following padding in hit target
    .padding(horizontal = 16.dp, vertical = 12.dp)
```

Versus padding before click, which excludes outer padding from the hit target. Review order for size, padding, clip, background, border, click, focus, semantics, graphics, and insets.

## Scaffold and insets

A top-level pattern commonly has:

```kotlin
Scaffold(
    topBar = { /* Material3 top app bar */ },
    snackbarHost = { SnackbarHost(snackbarHostState) },
) { innerPadding ->
    ScreenContent(
        modifier = Modifier.padding(innerPadding),
    )
}
```

Apply `innerPadding` exactly once. If a child consumes selected system insets itself, define that ownership explicitly. Avoid adding status/navigation bar padding both to `Scaffold` and its content.

Use `WindowInsets` for system bars, cutouts, gesture areas, and IME. Prefer inset padding/size/consumption APIs over copied dp constants. Verify gesture and three-button navigation.

## Adaptive decisions

Base high-level layout on available window size and posture:

```kotlin
val adaptiveInfo = currentWindowAdaptiveInfo(
    supportLargeAndXLargeWidth = true,
)
val windowSizeClass = adaptiveInfo.windowSizeClass
```

Current width classes are compact (<600dp), medium (600–839dp), expanded (840–1199dp), large (1200–1599dp), and extra-large (>=1600dp). Treat them as dynamic window properties, never device categories.

Use:

- `NavigationSuiteScaffold` when top-level navigation should adapt between bar and rail (or an explicitly selected drawer policy).
- `NavigableListDetailPaneScaffold` for list/detail content with adaptive panes and pane navigation.
- `NavigableSupportingPaneScaffold` when secondary content supports a main pane.
- A feed/canonical layout when the information architecture matches.
- `WindowAdaptiveInfo` posture/hinge data where fold state affects occlusion or pane placement.

Separate three concerns:

1. Destination/back-stack state.
2. Selected content identity.
3. Current visible pane arrangement.

A width change may alter arrangement; it must not fabricate a navigation event or discard selection.

## Responsive content

- Constrain text and forms to readable widths.
- Add whitespace, columns, or supporting panes at larger widths rather than scaling every control.
- Keep action proximity and reachable navigation appropriate to the current arrangement.
- Preserve feature parity across orientation/fold/window states.
- Support mouse, keyboard, D-pad, touch, and focus where target devices provide them.
- Use stable lazy keys and content types; never use collection position as identity when items can insert, remove, or reorder.

## Back and transitions

Predictive back is enabled by platform/target rules; verify the current requirements. Adaptive pane scaffolds provide explicit back behaviors. Choose based on the product contract rather than accepting a default unknowingly:

- Pop until scaffold arrangement changes.
- Pop until content changes.
- Pop until destination changes.
- Pop only the latest entry.

Test compact and multi-pane back behavior separately. A multi-pane selection change may not imply the same back result as navigating from list to detail in a compact window.
