# Compose UI testing

Source: [Testing Compose Multiplatform UI](https://kotlinlang.org/docs/multiplatform/compose-test.html).

Add `org.jetbrains.compose.ui:ui-test:<compose-version>` to `commonTest`. Common tests use `runComposeUiTest` on the `ComposeUiTest` receiver rather than JUnit `TestRule`. Desktop tests additionally need the matching `org.jetbrains.compose.desktop:desktop-jvm-<os>-<arch>:<compose-version>` runtime (`compose.desktop.currentOs` is deprecated in 1.12). Android device tests need a configured device source set, runner, manifest/activity, Android test artifacts, and debug manifest artifact.

Test behavior through semantics:
1. set content with deterministic state/fakes
2. find by text, role, content description, or intentional test tag
3. perform user action
4. assert visible/enabled/selected/state/error/output semantics
5. advance clock/wait for Compose idleness when controlled async/animation work exists

Cover state transitions and invariants: empty/loading/error/content, duplicate events, effect restart/disposal, restoration, locale/RTL/theme/density/large text, focus/keyboard/back, navigation/deep links, window resize, interop callbacks, and accessibility.

Use platform runners for platform contracts. Android emulator/device verifies instrumentation and system integration; iOS verifies touch/VoiceOver/native interop; desktop verifies AWT/window/keyboard; browser verifies DOM/Canvas environment, Wasm/JS loading, and accessibility.

Avoid fixed sleeps and incidental implementation selectors. Screenshot tests are platform-scoped because fonts, antialiasing, native popups, and rendering differ. A common semantics pass does not prove platform visuals or native interop.
