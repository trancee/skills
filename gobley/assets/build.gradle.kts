import gobley.gradle.GobleyHost
import gobley.gradle.cargo.dsl.jvm

plugins {
    kotlin("multiplatform") version "2.1.10"
    kotlin("plugin.atomicfu") version "2.1.10"
    id("dev.gobley.cargo") version "0.3.7"
    id("dev.gobley.uniffi") version "0.3.7"
}

kotlin {
    jvm()
    jvmToolchain(21)
}

cargo {
    builds.jvm {
        // Local proof only; declare shipped platform binaries for distribution.
        embedRustLibrary = (rustTarget == GobleyHost.current.rustTarget)
    }
}

uniffi {
    generateFromLibrary {
        packageName = "example.gobley"
    }
}

val jvmMain = kotlin.targets.getByName("jvm").compilations.getByName("main")
tasks.register<JavaExec>("interopSmoke") {
    dependsOn(jvmMain.compileTaskProvider)
    classpath = jvmMain.output.allOutputs + configurations.getByName("jvmRuntimeClasspath")
    mainClass.set("example.smoke.SmokeKt")
}
