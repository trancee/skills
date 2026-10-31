# Configuration and CI

## Choose the runtime SDK and test worker

1. RECORD compileSdk, targetSdk, app minSdk, test SDKs, Robolectric version, Gradle daemon JDK and test-worker JDK separately. compileSdk provides compile-time APIs; Robolectric's framework jar supplies runtime behavior. Default test SDK follows targetSdk, not compileSdk.
2. For 4.17, use the released SDK inventory, not the lagging README's 4.16.1 example. Known runtime APIs are 23–37. The library moved to Java 11 bytecode; newer SDK jars impose stricter worker-JDK floors:

| Runtime SDK | SDK jar Java floor |
| --- | ---: |
| 23–28 | 8 |
| 29–33 | 9 |
| 34–35 | 17 |
| 36–37 | 21 |

The effective worker floor is the maximum of library/dependency bytecode, SDK jar and build-tool requirements. Java 8/9 rows do not make Robolectric 4.17 runnable on Java 8/9. Prefer a repository-compatible JDK 17 or 21; apply the documented JDK 17+ opens from the setup asset to test workers, not only `org.gradle.jvmargs`.
3. SELECT behavior boundaries with `@Config(sdk = {33, 34})`; use numeric `sdk=33,34` in package properties. `@Config(minSdk = 33, maxSdk = 35)` selects known SDKs in that range. Do not combine an explicit sdk list with minSdk/maxSdk in one configuration.
4. TREAT `robolectric.enabledSdks` as an intersection/filter, not an SDK override. Check executed SDK variants and counts; a mismatching CI filter can remove intended coverage. Installing a platform via sdkmanager does not add it to Robolectric's inventory.

Sources: [4.17 release](https://github.com/robolectric/robolectric/releases/tag/robolectric-4.17), [SDK inventory and jar versions](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/robolectric/src/main/java/org/robolectric/plugins/DefaultSdkProvider.java), [SDK picker](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/robolectric/src/main/java/org/robolectric/plugins/DefaultSdkPicker.java).

## Resolve configuration precedence

1. PLACE package configuration at `src/test/resources/<package>/robolectric.properties`; the classpath-root file applies broadly. More-specific package files override broader values. Class/base-class annotations and then method annotations supply test-local overrides.
2. TRACE each field, rather than replacing whole configurations: explicit SDK selections replace earlier SDK selection; ordinary qualifiers replace, `+land` overlays; shadows append and instrumentedPackages union; non-default scalar fields override. Empty/default values generally inherit, not clear earlier values. To remove a suite-wide shadow, move it to its actual test/package scope rather than trying `shadows = {}` locally.
3. For a test application, use `@Config(application = TestApplication.class)` only when application initialization really needs substitution. Preserve production initialization when that is the behavior being checked.
4. KEEP modern AGP's merged manifest and binary resources. Do not apply historical `libraries`, `assetDir`, `resourceDir`, `packageName` configuration from old tutorials: these are absent from 4.17 Config. `manifest = Config.NONE` is only for genuinely manifest/resource-free setups; it is not a resource-error fix.

Sources: [configuration](https://robolectric.org/configuring/), [released Config and overlay](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/annotations/src/main/java/org/robolectric/annotation/Config.java), [build-system contract](https://robolectric.org/build-system-integration/).

## Preserve JUnit execution

USE `org.junit.Test` and `org.junit.runner.RunWith`; choose RobolectricTestRunner or AndroidJUnit4 with its declared dependency. Jupiter `@Test` does not invoke a JUnit 4 runner. If the repository already uses `useJUnitPlatform()`, add an aligned JUnit Vintage engine and platform launcher in testRuntimeOnly using its existing JUnit BOM; keep Robolectric tests JUnit 4. Do not switch the entire suite's engine merely to add Robolectric.

Source: [released Vintage integration](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/integration_tests/junit-vintage-engine/build.gradle.kts).

## Make runtime dependencies hermetic

1. DISTINGUISH Gradle dependency resolution from Robolectric's runtime Maven resolver. Gradle `--offline` alone does not stop framework-jar fetching.
2. With the default online resolver, cache both Gradle dependencies and runtime Maven artifacts. Runtime cache location: test-worker `maven.repo.local`, then localRepository in `~/.m2/settings.xml`, then `~/.m2/repository`. Warm every intended SDK, graphics mode and version; one passing SDK is not a complete matrix cache.
3. For explicit offline execution, provision exact framework artifacts from the released SDK provider. Default is preinstrumented jars with instrumentation suffix `i7` in 4.17. PUT correctly named jars in a **flat** directory, then configure the worker:

```kotlin
android.testOptions.unitTests.all {
    it.systemProperty("robolectric.offline", "true")
    it.systemProperty("robolectric.dependency.dir", file("ci/robolectric-jars").absolutePath)
}
```

A dependency.dir selects local resolution even without offline=true. offline=true without a directory looks in the worker's current directory, not its Maven cache. Preserve `robolectric.usePreinstrumentedJars=true` unless modifying instrumentation itself.
4. VERIFY an offline CI-equivalent run with network unavailable and all requested SDK variants executed. Resolve Gradle's dependencies before that run; include any separately needed native-runtime dependencies. Do not claim hermeticity from a warm online run.
5. For an approved mirror/proxy, configure test-worker system properties: `robolectric.dependency.repo.id`, `.repo.url`, `.repo.username`, `.repo.password`, `.proxy.host`, `.proxy.port`. Source credentials from existing secret providers; never commit or log values. JVM/Gradle `-D` properties are not assumed to propagate to a forked worker; set them on its Test task.

Sources: [documented properties](https://robolectric.org/configuring/#system-properties), [resolver selection](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/robolectric/src/main/java/org/robolectric/plugins/LegacyDependencyResolver.java), [flat filenames](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/robolectric/src/main/java/org/robolectric/internal/dependency/LocalDependencyResolver.java), [Maven cache](https://github.com/robolectric/robolectric/blob/0706415db828e1bdcf4f0c820784fa760d0185a2/plugins/maven-dependency-resolver/src/main/java/org/robolectric/internal/dependency/MavenDependencyResolver.java).

## Diagnose the first failing boundary

| Evidence | Action |
| --- | --- |
| No tests discovered / zero SDK variants | Check JUnit 4 imports, engine/filter, class visibility, variant task and enabledSdks intersection. |
| `Stub!` / method not mocked | Confirm Robolectric runner actually executed and instrumented framework jar loaded; do not enable returnDefaultValues. |
| SDK not known or requires newer Java | Compare released SDK inventory and actual worker JDK; upgrade the required dependency/worker, or select an explicitly accepted supported coverage set. |
| ResourceNotFound / missing Activity / bad theme | Check unitTests.isIncludeAndroidResources, namespace/R, owning variant's merged manifest, activity registration and theme. |
| Fetch/SSL/proxy failure | Inspect runtime resolver URL/cache separately from Gradle; correct approved network configuration without disabling TLS verification. |
| Native load failure | Check runtime artifact, OS/architecture, extraction permission and native dependencies; report unsupported native behavior rather than silently using legacy graphics. |
| Unexecuted main-loop tasks | Advance the responsible queue at the specified boundary; check async completion and dispose components/jobs. Do not blindly drain recurring tasks. |
| Reflection/module access failure | Check documented opens on test worker and compatible versions; avoid arbitrary broad export/open additions. |

RUN the exact failing class with `--stacktrace`; enable `robolectric.logging.enabled=true` on the worker temporarily when framework/resource resolution evidence is needed. Remove diagnostic settings after locating the cause.
