# Apple frameworks and XCFrameworks

Sources: [Apple framework tutorial](https://kotlinlang.org/docs/apple-framework.html) and [native binaries](https://kotlinlang.org/docs/multiplatform-build-native-binaries.html).

```kotlin
import org.jetbrains.kotlin.gradle.plugin.mpp.apple.XCFramework

kotlin {
    val xcf = XCFramework()
    listOf(iosArm64(), iosSimulatorArm64()).forEach { target ->
        target.binaries.framework {
            baseName = "Shared"
            isStatic = true
            xcf.add(this)
        }
    }
}
```

Framework tasks follow `link<BuildType>Framework<Target>`, e.g. `linkDebugFrameworkIosArm64`. Output is under `build/bin/<target>/<buildType>Framework`. XCFramework tasks include `assembleXCFramework`, `assemble<Name>DebugXCFramework`, and `assemble<Name>ReleaseXCFramework`.

All slices in a framework/XCFramework need the same base name and compatible public headers. Static versus dynamic affects embedding/linking/signing; choose from consumer packaging, not convenience.

## Exports

Only source-set `api` dependencies can be exported:
```kotlin
sourceSets.appleMain.dependencies { api(project(":dependency")) }
framework {
    export(project(":dependency"))
}
```

Export disables dead-code elimination for the dependency and increases binary/API size. Export is nontransitive by default. `transitiveExport=true` pulls all transitives and is not recommended; enumerate consumer-visible dependencies.

## Distribution metadata

Use `binaryOption` for `bundleId`, `bundleShortVersionString`, and `bundleVersion`. Include native binary licenses. Preserve module name, bundle ID, framework name, architectures, and exported API as distribution contract.

KDoc is embedded/exported by default where available. Dependency KDoc requires `-Xexport-kdoc` at dependency compilation and may reduce compiler-version compatibility; `exportKdoc=false` disables framework export.
