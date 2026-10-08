plugins {
    kotlin("multiplatform") version "2.4.0"
    id("ch.ubique.uniffi.plugin") version "1.3.1"
}

uniffi {
    generateFromLibrary {
        packageName = "example.ubique"
    }
}

kotlin {
    jvm()
    jvmToolchain(21)
}

val jvmMain = kotlin.targets.getByName("jvm").compilations.getByName("main")
tasks.register<JavaExec>("interopSmoke") {
    dependsOn(jvmMain.compileTaskProvider)
    classpath = jvmMain.output.allOutputs + configurations.getByName("jvmRuntimeClasspath")
    mainClass.set("example.smoke.SmokeKt")
}
