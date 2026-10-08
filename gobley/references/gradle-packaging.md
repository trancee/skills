# Gradle builds, packaging, and consumers

## Target/build ownership

Cargo tasks follow declared Kotlin targets. `cargo metadata` discovers the package and Rust source dependencies. Set `cargo.packageDirectory` to the package directory, not a guessed parent or arbitrary `src` directory. Preserve workspace dependency/features ownership.

Discover effective task names with `./gradlew :module:tasks --all`. Run narrow Kotlin tasks; Gobley connects Cargo builds and binding generation. Use `--stacktrace` for failure ownership and `--info` only when concrete invocation/artifact evidence is needed. IDE sync can build Rust; disabling `generateDuringSync` does not eliminate Native cinterop generation.

## Android

- The Cargo plugin obtains SDK/NDK and ABI selection from the Android configuration: `android.ndkVersion` and `defaultConfig.ndk.abiFilters`.
- Package matching `cdylib` files per ABI plus required dependent libraries. Keep generated JNA ProGuard/consumer rules; test R8/minified release independently of debug.
- Local Android unit tests execute in the **host JVM**, not Android. They require a host shared library/JNA JAR. `androidUnitTest` controls host-runtime selection; a successful unit-test compile does not prove native loading.
- Consumer modules referencing a Gobley producer need `dev.gobley.rust` for runtime/config propagation, including indirect consumers. Separately published producers need explicit runtime-classifier dependencies.
- Recheck the consumer's AGP/KMP Android plugin integration before migrating versions. The 0.3.7 examples use `com.android.library` + `androidTarget`; do not infer compatibility with a newer Android-KMP plugin solely from those examples.

## JVM host proof versus release matrix

Default JVM builds can attempt targets whose cross linkers are absent. For a local proof only:

```kotlin
import gobley.gradle.GobleyHost
import gobley.gradle.cargo.dsl.jvm

cargo {
    builds.jvm {
        embedRustLibrary = (rustTarget == GobleyHost.current.rustTarget)
    }
}
```

For distribution, replace this filter with the **shipped target set** and build each on a capable host. Runtime binaries are packaged in separate JARs with JNA resource prefixes. Release classifiers default to `rustTarget.jnaResourcePrefix`; debug adds `-debug`. Inspect the actual archive names/entries, particularly when JVM target names or resource prefixes are customized. Match architecture to the **running JVM**, including Rosetta, rather than physical hardware alone.

`maven-publish` on KMP automatically adds runtime JARs unless `publishJvmArtifacts=false`. Published consumers must resolve Kotlin classes/metadata **and** appropriate native runtime classifiers. Kotlin Gradle metadata alone does not supply all classifier JARs.

```kotlin
// Existing jvmMain source set; replace coordinate/classifier with inspected artifacts.
kotlin.sourceSets.named("jvmMain") {
    dependencies {
        runtimeOnly(project.dependencies.variantOf(libs.coreJvm) {
            classifier("linux-x86-64")
        })
    }
}
```

Validate using a separate consumer with only the intended Maven repository, not producer project outputs or incidental local library paths.

## Native, variants, and features

Native targets link the Rust `staticlib` and use generated C headers/cinterop. Apple targets require macOS/Xcode. Device and simulator targets are not interchangeable.

```kotlin
import gobley.gradle.Variant

cargo {
    jvmVariant = Variant.Release
    jvmPublishingVariant = Variant.Release
    nativeVariant = Variant.Release
}
```

Set these only for the intended release workflow; preserve debug behavior separately. `jvmVariant` normally defaults Debug, publication normally Release, and `nativeVariant` normally Debug outside Xcode-provided environment. An application referencing the producer can still use the debug JVM binary; publication settings alone do not fix app release selection.

Cargo `features` accumulate across scopes when using `.add`/`.addAll`; `.set` replaces inherited selections. Configure custom profiles using `gobley.gradle.cargo.profiles.CargoProfile`. Ensure generation and runtime builds expose the same API-affecting features.

## Dependent native libraries

Packaging and loading are separate gates:

```kotlin
import gobley.gradle.cargo.dsl.jvm

cargo {
    builds.jvm {
        dynamicLibraries.add("myaudio")
        dynamicLibrarySearchPaths.add(layout.projectDirectory.dir("native-libs").asFile)
    }
}
```

Configure the loader separately in the crate's `uniffi.toml` (0.3.7 does not expose this option in its generation DSL):

```toml
jvm_dynamic_library_dependencies = ["myaudio"]
```

Use names without `lib` prefixes/extensions. `dynamicLibraries` copies binaries; bindgen dependency settings control loading. Search includes Cargo output/build-script `OUT_DIR` and Android NDK directories; custom locations need explicit paths. On macOS/Linux verify install names/SONAMEs and transitive runtime dependencies, not just presence in a ZIP.

For Android C++ use `dynamicLibraries.add("c++_shared")` when the crate/dependencies consistently use that runtime. Avoid silently mixing static and shared C++ runtimes.

Sources: [Cargo configuration and publication](https://gobley.dev/docs/gradle-plugins/cargo), [Rust consumer plugin](https://gobley.dev/docs/gradle-plugins/rust), [pinned Cargo DSL](https://github.com/gobley/gobley/tree/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/build-logic/gobley-gradle-cargo/src/main/kotlin/dsl), [UniFFI configuration](https://gobley.dev/docs/bindgen#bindgen-configuration).
