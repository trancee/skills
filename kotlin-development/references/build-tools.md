# Kotlin build

Preserve wrapper/DSL/plugin aliases/dependency policy.

## Gradle

- use `./gradlew`/`gradlew.bat`
- inspect `settings.gradle.kts`, affected `build.gradle.kts`, `gradle.properties`, `gradle/libs.versions.toml`
- version change -> live [KGP/Gradle/AGP table](https://kotlinlang.org/docs/gradle-configure-project.html); resolution success != supported
- compiler config=`compilerOptions {}`; `kotlinOptions {}` deprecated
- precedence: extension default < target override < task override
- JVM: existing Java toolchain; align `jvmTarget`+`targetCompatibility`; Gradle>=8 mismatch default=error

Discover then run owning task:
```bash
./gradlew tasks --all
./gradlew projects
```
Typical JVM: `compileKotlin`, `compileTestKotlin`, `test`, `check`, `build`; Android/KMP use discovered variant/target names. Failure: `--stacktrace`; resolution/args only: `--info`/`--debug`. Debug key: JVM/JS/Wasm `Kotlin compiler args:`; Native `Arguments =`.

## Maven

JVM only. Use `./mvnw`/`mvnw.cmd`. Inspect `pom.xml`, parent management, profiles, `kotlin-maven-plugin`. Align plugin+stdlib via existing property/management. Mixed Kotlin/Java: preserve plugin order; Kotlin compile before Java if Java depends on Kotlin.
```bash
./mvnw test
./mvnw verify
```
Use existing module selector. Never duplicate parent/BOM version control.

## Standalone

Only small program/script/repro:
```bash
kotlinc Main.kt -include-runtime -d app.jar
java -jar app.jar
```
Library omits `-include-runtime`; consumer supplies runtime. `kotlinc -help`; `-X` unstable.

## Upgrade

READ [releases](https://kotlinlang.org/docs/releases.html)+destination migration guide. Update kotlinx/compiler plugins only for compatibility. Separate upgrade from behavior fix unless compiler is cause. Authoring snapshot=Kotlin 2.4.10 on 2026-08-30; live docs win.
