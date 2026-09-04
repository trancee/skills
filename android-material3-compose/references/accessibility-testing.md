# Accessibility, previews, testing, and runtime proof

## Accessibility contract

Material3 components carry role, state, action, and minimum-size behavior. Inspect before adding semantics; redundant parent and child semantics often produce duplicate announcements.

Add only missing meaning:

- `contentDescription` for meaningful images and icon-only actions; use `null` for decorative icons.
- `stateDescription` for domain-specific toggle/status wording.
- `heading()` for navigable content hierarchy.
- `error()` plus visible localized error text for invalid input.
- `liveRegion` for important transient updates; prefer polite and avoid frequent updates.
- `paneTitle` for custom sheet/dialog/pane surfaces.
- `progressBarRangeInfo` for custom determinate progress.
- `collectionInfo` / `collectionItemInfo` when a custom collection otherwise loses context.
- Custom actions when gesture-only behavior needs an accessible equivalent.

Use `clearAndSetSemantics` only after inspecting merged and unmerged trees; it hides descendant semantics. Make labeled parent rows selectable/toggleable and pass a null interaction callback to the child control only when this produces one correct semantic node.

Verify:

- 48dp minimum touch targets without shrinking semantics through custom layout.
- 4.5:1 contrast for normal text and 3:1 for large text/graphics, plus visible focus and non-color state cues.
- TalkBack order, announcements, roles, states, errors, actions, headings, dialogs/sheets, and focus restoration.
- Switch Access/keyboard/D-pad reachability and no gesture-only operation.
- Font scales up to 200%, display size, RTL, long translations, bold/high-contrast text settings, and animation scale disabled.
- Input labels, hints versus persistent labels, autofill, IME action, validation, and password behavior.

## Preview matrix

Keep screen composables parameterized by state/events so previews require no database, network, ViewModel, or Activity owner.

Cover the smallest valuable matrix:

- Light and dark branded schemes.
- Dynamic-color examples when enabled.
- Compact and expanded dimensions; medium when layout differs.
- Default and largest supported font scale.
- One long/RTL locale when text/layout changes.
- Loading, empty, content, error, selected, disabled, dialog/sheet, and keyboard/IME state as relevant.

Use multipreview annotations to reduce repetition. A preview confirms design-time rendering only; it does not prove system bars, runtime resources, accessibility services, navigation, focus, or lifecycle.

## Behavioral UI tests

Test user-observable semantics and transitions:

```kotlin
@get:Rule
val composeRule = createAndroidComposeRule<MainActivity>()

@Test
fun invalidSubmission_showsAccessibleError() {
    // Arrange
    composeRule.onNodeWithText("Email").performTextInput("not-an-email")

    // Act
    composeRule.onNodeWithText("Continue").performClick()

    // Assert
    composeRule.onNodeWithText("Enter a valid email").assertIsDisplayed()
}
```

Prefer label/text/role/state matchers over test tags. Add a test tag only when no stable user-facing semantic selector can identify the node. Inspect with `printToLog` or the Layout Inspector when matching fails.

Control Compose idleness and `mainClock`; never sleep. Inject deterministic state and clocks. Keep test data local and disable infinite animations.

High-value contracts include:

- Validation and error recovery.
- Selected/checked/toggled state and enabled rules.
- Snackbar/dialog/sheet action and dismissal.
- Navigation/back and adaptive pane transitions.
- Save/restore behavior promised to users.
- Custom control role/state/action semantics.
- Runtime window resize preserving content and selection.

Do not assert implementation wiring, callback forwarding, internal composable names, exact semantics-tree shape, or incidental wording.

## Screenshot tests

Use screenshot/golden tests only for a visual contract that semantics tests cannot defend: theme tokens, component geometry, edge-to-edge/insets, or a prior visual regression.

Stabilize:

- Library/font/device-image versions.
- Density, dimensions, locale, layout direction, font scale, theme, and dynamic-color seed.
- Clock/animations, input cursor, and asynchronous image/data loading.
- System-bar presence and API level.

Review meaningful diffs; never mass-accept new goldens to make CI green.

## Runtime proof matrix

Launch the actual app/Activity and exercise only affected but real paths:

| Axis | Required examples |
| --- | --- |
| Theme | Light, dark; dynamic on/off when supported |
| Window | Compact, medium/expanded where layout changes; resize while active |
| System UI | Gesture and three-button navigation, status/cutout, IME |
| State | Loading/empty/content/error plus changed interaction |
| Access | TalkBack, keyboard/D-pad if applicable, 200% font scale, RTL/long locale |
| Lifecycle | Rotate, background/foreground, process restoration if promised |
| Navigation | Forward, system back, predictive back, deep link if changed |

Run the narrow Gradle compile/test tasks for affected modules, then install and launch a debuggable or release-like build on an emulator/device. Preview and JVM compilation alone are insufficient for Android UI behavior.

## Performance

First reproduce measured jank or excess work in a release-like build. Then inspect system traces, recomposition/highlight tooling, layout inspector, and stability reports.

Common causes:

- Reading rapidly changing state too high in the tree.
- Missing lazy keys/content types.
- Sorting/filtering or allocating objects during every composition.
- Unstable parameters forcing broad recomposition.
- Synchronous image/data work on the main thread.
- Backward writes or effects with incorrect keys.

Move work or stabilize data only after evidence identifies the path. Re-run the original trace/scenario; a lower recomposition count is not itself a user-visible performance result.
