# Android testing branches

## Choose lifecycle ownership

1. PREFER AndroidX `ActivityScenario` for valid lifecycle transitions and tests shared with instrumentation. Declare `androidx.test:core`; for AndroidJUnit4 declare `androidx.test.ext:junit`. Use aligned versions from the repository. Access activities through `scenario.onActivity`, then `moveToState`, `recreate`, and close via try-with-resources / Kotlin `use` or ActivityScenarioRule.
2. USE `Robolectric.buildActivity` and ActivityController when testing individual Android callbacks or needing Robolectric-only lifecycle control. `setup()` reaches a resumed activity; always close the controller. Follow valid transitions; `pause().stop()` is not equivalent to `destroy()`.
3. ASSERT observable saved state, registration lifetime, returned result, navigation component/extras, or rendered content. Robolectric's recorded started Intent does not prove the destination Activity ran; launch it separately if its behavior is in scope.
4. For FragmentScenario, declare the matching fragment-testing artifacts and host manifest according to the current AndroidX documentation; close it and use its lifecycle APIs rather than calling fragment callbacks directly.

Sources: [AndroidX integration](https://robolectric.org/androidx_test/), [first test and controller cleanup](https://robolectric.org/writing-a-test/), [ActivityScenario contract](https://developer.android.com/reference/androidx/test/core/app/ActivityScenario).

## Control scheduling and clocks

Robolectric 4.17 defaults to PAUSED. Explicit `@LooperMode(LooperMode.Mode.PAUSED)` documents scheduling-sensitive tests. Its main-loop posts wait until execution is requested; setup and AndroidX/Espresso helpers can idle that loop themselves. Background loopers execute asynchronously on their own threads. PAUSED is not an all-threads scheduler.

```java
Handler handler = new Handler(Looper.getMainLooper());
handler.postDelayed(callback, 1000);
shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(999));
// Assert callback's consumer-visible effect has not happened.
shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(1));
// Assert the effect happened exactly at the requested deadline.
```

1. USE `shadowOf(looper).idle()` for currently due work and `idleFor(Duration)` for a bounded virtual-time step. Blanket `runToEndOfTasks()` can hide ordering bugs or hang on recurring work; advance only the relevant deadline.
2. KEEP each clock owner explicit: Android SystemClock/Looper virtual time, coroutine TestCoroutineScheduler time, Compose mainClock, injected app Clock, and real executor completion are distinct controls. Advancing a Robolectric looper does not advance coroutine delay or guarantee an executor completed.
3. For coroutine tests, route dispatcher/scope ownership to `kotlin-coroutines`; inject deterministic dispatchers, advance their scheduler, then idle the Looper for any posted Android effects. Cancel jobs and restore dispatcher changes at teardown.
4. For real background execution, await its actual completion through the app's synchronization boundary; do not replace synchronization with Thread.sleep or assume PAUSED implies synchronous execution.
5. MIGRATE legacy Scheduler/foreground/background scheduler calls to the responsible ShadowLooper or an injected executor. LEGACY LooperMode is deprecated and unsupported above API 36. Do not confuse it with LEGACY graphics mode.

Source: [released LooperMode semantics](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/annotations/src/main/java/org/robolectric/annotation/LooperMode.java).

## Exercise resources and configuration

1. USE the owning AGP variant's merged resources, assets, manifest and generated R. Assert resource-dependent output, not just successful inflation. Keep tests in src/test; resource fixtures live in the source sets actually merged by that variant.
2. USE `@Config(qualifiers = "fr-rFR-w360dp-h640dp-xhdpi")` for a fresh test configuration. Qualifiers follow Android resource ordering without a `values-` prefix; `+land` overlays previous qualifiers, while `land` replaces them.
3. To simulate a configuration change within a controller test, call `RuntimeEnvironment.setQualifiers("+land")` then `controller.configurationChange()`. The qualifier setter updates resources but does not itself notify/recreate existing activities. Obtain the current Activity again afterward.
4. USE normal asset/resource APIs and AndroidX ApplicationProvider for Context when that dependency already exists. Avoid hardcoded workstation resource paths or mock Resources/Context when Android behavior is the reason for the test.

Sources: [device configuration](https://robolectric.org/device-configuration/), [build-system contract](https://robolectric.org/build-system-integration/).

## AndroidX, Espresso and Compose

1. ADD only APIs actually used to testImplementation: `androidx.test:core`, `androidx.test.ext:junit`, `androidx.test.espresso:espresso-core`. Keep their versions aligned through the repository's existing ownership. Espresso view matching/actions are supported with Robolectric; UIAutomator/system-app/device interaction still needs an emulator/device.
2. For Android Compose local tests, keep the existing Compose compiler/BOM configuration; add `androidx.compose.ui:ui-test-junit4` to testImplementation and `androidx.compose.ui:ui-test-manifest` to debugImplementation when using the supplied test host. With `createAndroidComposeRule<OwnActivity>()`, register that real Activity in the tested manifest instead of assuming the generic host supplies it.
3. USE RobolectricTestRunner (or configured AndroidJUnit4), JUnit 4 `@get:Rule`, and `createComposeRule` / `createAndroidComposeRule`. Assert semantics after a real action and recreation when state retention matters; preserve Compose's own idling/mainClock semantics. Prefer its waiting APIs for composition rather than blindly pumping every queue.
4. Treat native rendering/screenshot requirements as a separate branch; a semantics assertion is not a pixel-fidelity check. Compose Multiplatform non-Android tests use that platform's test runtime, not Robolectric in commonTest.

Sources: [AndroidX/Espresso support](https://robolectric.org/androidx_test/), [released Compose build configuration](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/integration_tests/composeui/build.gradle.kts), [released Compose rule example](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/integration_tests/composeui/src/test/java/org/robolectric/integrationtests/composeui/FocusRequesterTest.kt).

## Custom shadows

1. USE a built-in shadow's documented API first. Add a custom shadow only for an actual missing framework boundary; prefer injected app dependencies for app-owned code. Register narrowly with `@Config(shadows = CustomShadow.class)`.
2. Match the **declaring class**, method signature/staticness and required API range. Supply a public no-arg shadow constructor and `@Implements` / `@Implementation`; preserve the shadow inheritance chain if replacing an existing framework shadow.
3. Retrieve a custom shadow with typed `Shadow.extract(realObject)`, not a generated `Shadows.shadowOf` overload. `@RealObject` methods are still intercepted; calling the same shadowed method recursively is not a call-through. Use a verified `Shadow.directlyOn` overload when calling real implementation is necessary.
4. If static shadow state is necessary, reset it explicitly in teardown unless a registered ShadowProvider/reset path has been verified. Verify isolation by running with unrelated tests and reversed test order.
5. ASSERT the app's response to the injected boundary, not merely that the shadow returned its configured value. A custom shadow is a simulation assumption; it does not establish Android/OEM behavior.

Sources: [shadow contract](https://robolectric.org/extending/), [architecture and reset lifecycle](https://robolectric.org/architecture/).

## Native graphics

SELECT `@GraphicsMode(GraphicsMode.Mode.NATIVE)` when actual Canvas/Bitmap pixels or native text/drawing behavior are the requested contract. LEGACY graphics contains no-ops/fakes; do not silently substitute it for a pixel test after native loading fails. Run the native pixel example described in the core skill.

4.17's default native loader accepts Linux x86_64, Windows x86_64, and macOS x86_64/aarch64. This is native-runtime support, not a guarantee that every Robolectric feature works on every host. Verify packaged native libraries, OS dependencies and executable/extractable temporary storage. Android API/native code selection still matters. Host rendering is not proof of device GPU/OEM/font equivalence; keep device verification for those contracts.

Sources: [graphics modes](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/annotations/src/main/java/org/robolectric/annotation/GraphicsMode.java), [native loader support](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/nativeruntime/src/main/java/org/robolectric/nativeruntime/DefaultNativeRuntimeLoader.java).
