# Runnable examples

## Install into a disposable Android module

USE a disposable Android application module, not an existing production source tree, for the bundled demonstration. Preserve a compatible Gradle/AGP/JDK tuple. The example namespace is `example.robolectric`; compileSdk must expose API 34 constants, minSdk can be 23, and runtime targets are explicitly APIs 33/34. Merge the setup asset into that module.

COPY these package-root assets to the exact module-relative destinations:

| Asset | Destination |
| --- | --- |
| assets/CounterActivity.java | src/main/java/example/robolectric/CounterActivity.java |
| assets/CounterActivityTest.java | src/test/java/example/robolectric/CounterActivityTest.java |
| assets/AndroidManifest.xml | src/main/AndroidManifest.xml |
| assets/counter.xml | src/main/res/layout/counter.xml |
| assets/strings.xml | src/main/res/values/strings.xml |
| assets/strings-fr.xml | src/main/res/values-fr/strings.xml |
| assets/NativeGraphicsTest.java | src/test/java/example/robolectric/NativeGraphicsTest.java |

USE these Gradle repositories in the existing settings/dependency owner: google() and mavenCentral(); make the AGP plugin available through the pluginManagement repositories. If AndroidX transitive dependencies require the repository's AndroidX setting, enable android.useAndroidX=true. Point the disposable module at an installed compileSdk through ANDROID_HOME or local.properties; keep machine paths out of committed assets.

RUN the module's `testDebugUnitTest` task. CounterActivityTest contains three behaviors, each executed on APIs 33 and 34: an update is absent at 999 ms and present at 1000 ms, clicked count survives Activity recreation, and French resources select the French label. NativeGraphicsTest uses API 34 and checks both an inside red pixel and an outside transparent pixel. Expected: seven passing invocations, not merely discovered classes.

Verified tuple: Robolectric 4.17, JUnit 4.13.2, AGP 9.3.0, Gradle 9.6.1, JDK 21, compileSdk 37, targetSdk 34, minSdk 23, Linux x86_64. This is an exercised example tuple, not a universal compatibility matrix.

For a consumer project, ADAPT the behavior and package names to its actual Activity/resources; do not copy this counter app into production or keep tests that only assert sample constants. Kotlin equivalents use `@RunWith(RobolectricTestRunner::class)`, `@Config(sdk = [33, 34])`, `@LooperMode(LooperMode.Mode.PAUSED)`, and controller `.use { ... }`.

## Verification report

REPORT the exact module/variant, Robolectric and JUnit engines, Gradle/AGP/worker-JDK tuple, executed SDK/qualifier cases, observed lifecycle/looper/resource output, runtime fetching/offline state, and any unverified native/device requirements. Distinguish a passing simulated callback/Intent from actual OS/hardware execution.
