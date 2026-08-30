# Resources, adaptive UI, and accessibility

Sources: [resources](https://kotlinlang.org/docs/multiplatform/compose-multiplatform-resources.html), [resource setup](https://kotlinlang.org/docs/multiplatform/compose-multiplatform-resources-setup.html), [platform differences](https://kotlinlang.org/docs/multiplatform/compose-platform-specifics.html), and [accessibility](https://kotlinlang.org/docs/multiplatform/compose-accessibility.html).

Add `org.jetbrains.compose.components:components-resources:<compose-version>` to the consuming shared source set. (`compose.components.resources` is deprecated in Compose 1.12.) Place content under `<sourceSet>/composeResources/{drawable,font,values,files}` and use generated `Res` accessors. Provide an unqualified default before language/region, light/dark, or density variants. Qualifier order/case is significant.

Resources may live in any module/source set with Compose 1.6.10+, Kotlin 2.0+, Gradle 7.6+. Published artifacts include resources under that tuple. Android library generated resources need AGP 8.8+ and `androidResources.enable = true`.

Most resources load synchronously; raw files and web resources are exceptions. Do not buffer large raw media in composition. Use `getUri()` for system/external APIs and explicitly handle async web loading/failure.

Adaptive UI uses constraints, insets, density, input mode, and window class—not target-name checks alone. Verify keyboard/safe area, mouse versus touch/multitouch, scroll physics, platform fonts/text rasterization, focus, and back behavior.

Accessibility lives in the semantic tree. Native/custom controls need meaningful label/content description, role, state description, actions, enabled/error state, focus, and traversal. Use `testTag` only as a stable automation identifier; it does not replace user-facing semantics.

Test assistive technology on real targets: TalkBack/Android tooling, VoiceOver/XCTest, desktop screen reader/keyboard, and browser accessibility tree. Cross-platform screenshot baselines must tolerate intentional font/rasterization differences.
