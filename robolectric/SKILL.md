---
name: robolectric
description: "Configures, writes, runs, and troubleshoots Robolectric Android JVM tests. Use for Gradle setup, Android resources and lifecycle, PAUSED loopers, SDK and qualifier matrices, AndroidX integration, custom shadows, and CI dependency resolution. Don't use for pure JVM logic tests, device instrumentation, real Bluetooth or hardware validation, or general Gradle migrations."
compatibility: "Android JVM test module with compatible Gradle/AGP/JDK and Android SDK. Baseline Robolectric 4.17/JUnit 4; APIs 34–35 require worker Java 17+, APIs 36–37 Java 21+. Runtime framework jars need network access or explicit offline provisioning; native features have host constraints."
metadata:
  category: "testing-quality"
  source: "https://robolectric.org/"
  sourceVersion: "Robolectric 4.17@0706415db828e1bdcf4f0c820784fa760d0185a2; official docs read 2026-10-31"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-31T14:54:05+01:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-31T14:54:05+01:00"
---

# Robolectric

## Step 1: Establish the Android test boundary

1. DEFINE setup | behavior test | lifecycle/resources | scheduling | SDK/qualifier coverage | AndroidX/Compose | custom shadow | CI/download failure | upgrade.
2. IDENTIFY the owning Android module, variant, source sets, Gradle wrapper, AGP, test engine, test-worker JDK, compileSdk/targetSdk/minSdk, AndroidX/Compose version ownership, and required Android behavior.
3. USE Robolectric for Android framework behavior on a host JVM. Keep pure Kotlin/Java logic in ordinary unit tests; use device/emulator instrumentation for actual permissions/system services, Bluetooth/radio, OEM, GPU, or cross-app behavior. A shadow's recorded request is not proof the real OS executed it.
4. READ the current [setup docs](https://robolectric.org/getting-started/), [stable release](https://github.com/robolectric/robolectric/releases/latest), and requested-version source before changing dependencies. The pinned 4.17 source overrides lagging README examples and historical documentation fields. Route general build migration to `kotlin-gradle`, coroutine scheduling to `kotlin-coroutines`, Android Compose implementation to `android-material3-compose`.

Completion: exact consumer-visible behavior, Android simulation boundary, module/variant and verification command are known.

## Step 2: Configure the existing module

1. READ [configuration and CI](references/configuration-ci.md) for worker-JDK/SDK compatibility, engine selection, configuration precedence, upgrades, runtime downloads or failures.
2. MERGE [Gradle setup](assets/gradle-setup.gradle.kts) into the existing Android module's owning configuration; preserve its plugins, repositories, version catalog and toolchain. Required: testImplementation Robolectric and JUnit 4; unitTests.isIncludeAndroidResources=true for manifest/resources; documented opens on JDK 17+ test workers.
3. PLACE JVM tests in `src/test/java` or `src/test/kotlin`, not `src/androidTest`. Use `org.junit.Test` with RobolectricTestRunner, or declared AndroidJUnit4. Existing JUnit Platform suites need an aligned Vintage runtime for these JUnit 4 tests, not Jupiter annotations on a Robolectric runner class.
4. USE the tested variant's merged manifest/binary resources and generated R. Keep Activity registration, theme and app namespace accurate. Do not use returnDefaultValues or Config.NONE to conceal missing runner/resource setup.
5. SELECT a supported runtime SDK explicitly when the app target is outside the supported inventory, only with accepted coverage scope. compileSdk and installed Android SDK platforms do not define Robolectric runtime support. Verify both daemon and worker JDK; they may differ.

Completion: dependency resolution, runner, manifest/resources and worker-JDK/SDK contract are valid for the intended tests.

## Step 3: Exercise a real app behavior

1. READ [Android testing branches](references/android-testing.md) for ActivityScenario/controller lifecycle, qualifiers, loopers, AndroidX/Espresso/Compose, custom shadows or native rendering.
2. PREFER ActivityScenario for AndroidX lifecycle tests; use ActivityController for precise callback control. Close either owner. Assert a real action's output/state transition, including retained state or disposal when those are the contract.
3. For resources, assert the actual localized/qualified content or asset behavior. For navigation, compare the recorded Intent's component and relevant extras; test destination behavior separately if required.
4. For custom shadows, use built-in documented controls first; otherwise register the smallest shadow at the actual declaring-class/API boundary. Assert the app's reaction, preserve isolation, and state the simulation assumption.
5. For a new setup or a concrete runnable baseline, READ [example installation](references/examples.md) and copy its listed assets into a disposable module. The counter examples exercise real Activity lifecycle, delayed Looper work and compiled localized resources; the native example checks actual Canvas pixels.

Completion: the test reaches the actual app path and asserts its requested observable behavior, rather than wiring, mock echoes, successful construction or sample constants alone.

## Step 4: Make timing and coverage intentional

1. USE PAUSED LooperMode for scheduling-sensitive tests. Assert the effect before the deadline, advance the responsible ShadowLooper by bounded Duration, then assert after it. Setup and AndroidX helpers can auto-idle; background loopers/executors are not made synchronous by PAUSED.
2. KEEP Android Looper time, coroutine scheduler, Compose test clock, injected application clock and executor completion separate. Advance/await the actual owner and cancel test-owned jobs/components at teardown.
3. CHOOSE SDKs at behavior boundaries with `@Config(sdk = {33, 34})`; choose qualifiers for the actual locale/orientation/density/night contract. Prefer a focused explicit matrix over ALL_SDKS unless exhaustive coverage is requested.
4. CONFIRM the worker's enabledSdks intersection does not remove intended variants. A green build with zero/missing test cases is not SDK coverage.
5. For native drawing, select NATIVE graphics and verify its host library works; a legacy graphics fallback cannot prove pixels. Keep real-device fidelity claims out of host-only results.

Completion: deadlines, async completion, lifecycle cleanup and every requested SDK/qualifier/native case have observable evidence.

## Step 5: Run and diagnose

RUN the owning task, substituting the real module and test class:

```bash
./gradlew :app:testDebugUnitTest --tests 'com.example.FeatureTest' --stacktrace
./gradlew :app:testDebugUnitTest
```

1. CHECK Gradle/XML reports for executed cases and SDK variants; run the affected module's full local-test task after the focused case so isolation failures remain visible.
2. On failure, follow the first failing boundary in the configuration/CI reference: runner/engine, SDK/JDK, merged resources, runtime fetch, native loader, then app behavior. Enable worker logging temporarily only when evidence needs it.
3. For CI, provision both build dependencies and runtime framework jars. Verify offline behavior explicitly; Gradle --offline alone is not hermetic Robolectric execution.
4. For upgrades, compare release changes against actual imports/shadows/runtime jars and migrate affected callers in one cutover. In 4.17, AndroidVersions was removed and LEGACY loopers do not support API 37; use Android Build constants and PAUSED loopers, not compatibility aliases.

Completion: focused and full affected-module commands pass with intended cases executed; failing boundary or missing host prerequisite is explicit.

## Step 6: Report the evidence

REPORT versions/module/task, executed SDK and qualifier cases, observed behavior, async/lifecycle cleanup, runtime download/offline state and unverified hardware/native fidelity using the fields in the example reference. Separate simulated Android evidence from device evidence; do not claim blanket Android compatibility from one host SDK.

## Error handling

- Pure app logic only -> ordinary JVM tests; retain Robolectric only where Android execution is required.
- Unsupported SDK/worker -> align released Robolectric/runtime/JDK tuple; do not lower requested coverage silently.
- Main-loop queue warning -> inspect the required completion deadline and disposal; do not drain unrelated recurring work to suppress it.
- Stale tutorial fields -> inspect released Config/source and current AGP resource contract before copying configuration.
- Host cannot load required native behavior -> finish reachable checks and name the missing OS/architecture/library prerequisite; no fake passing fallback.
