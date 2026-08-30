# Legacy binary-compatibility-validator

Source: [Kotlin/binary-compatibility-validator](https://github.com/Kotlin/binary-compatibility-validator). Current 0.18.1 is in maintenance mode. It requires Gradle 6.1.1+ and Kotlin 1.6.20+.

Run the build on a runtime supported by the plugin's bytecode reader. BCV 0.18.1 fails under JDK 25 with `Unsupported class file major version 69`; JDK 21 is verified.

## Apply

```kotlin
plugins {
    id("org.jetbrains.kotlinx.binary-compatibility-validator") version "<BCV_VERSION>"
}
```

Apply once in the root project; it configures subprojects.

Tasks:
- `apiDump`: overwrite human-readable reference `.api` files under `api/` by default
- `apiCheck`: compare current API with reference; added to `check`/`build`

Configuration:
```kotlin
apiValidation {
    ignoredProjects.add("benchmarks")
    ignoredPackages.add("com.example.internal")
    ignoredClasses.add("com.example.BuildConfig")
    nonPublicMarkers.add("com.example.InternalApi")
    apiDumpDirectory = "api"
    validationDisabled = false
}
```

Prefer narrow class/annotation exclusions. A public declaration appearing unexpectedly is evidence to inspect source visibility before adding an ignore.

## Final JAR input

Default JVM dumps use compiled classes. When shading, relocating, excluding, or otherwise transforming output, configure `apiBuild.inputJar` from the actual `Jar`/`shadowJar` archive provider. Confirm task dependencies and compare dump with archive contents.

## Experimental KLib path

KLib validation requires Kotlin 1.9.20+ and explicit experimental opt-in. It produces `<project>.klib.api`. `strictValidation=true` fails when the host cannot compile a target; default behavior can preserve/infer unsupported-target sections. Set a stable `rootProject.name` because the library name enters the dump.

Do not choose this maintenance-mode plugin for new features that exist in KGP built-in validation. Preserve it when migration risk exceeds the requested scope.
