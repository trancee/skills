# Dokka Maven and CLI

Sources: [Maven guide](https://kotlinlang.org/docs/dokka-maven.html) and [CLI guide](https://kotlinlang.org/docs/dokka-cli.html).

## Maven

```xml
<plugin>
  <groupId>org.jetbrains.dokka</groupId>
  <artifactId>dokka-maven-plugin</artifactId>
  <version>${dokka.version}</version>
  <executions>
    <execution>
      <phase>pre-site</phase>
      <goals><goal>dokka</goal></goals>
    </execution>
  </executions>
</plugin>
```

Run `./mvnw dokka:dokka`; default output is `target/dokka`. `dokka:javadoc` and `dokka:javadocJar` are experimental. Other formats require same-version entries under `dokkaPlugins`. Inspect the effective POM: plugin management alone does not execute a goal.

Useful options include `moduleName`, `outputDir`, `failOnWarning`, `offlineMode`, `sourceDirectories`, `documentedVisibilities`, `reportUndocumented`, `suppressedFiles`, `includes`, `classpath`, `samples`, source/external links, and per-package options.

## CLI

Prefer Gradle/Maven when available: CLI requires complete manual source-set and plugin classpaths.

1. Download same-version `dokka-cli`, `dokka-base`, and `analysis-kotlin-symbols`; add HTML runtime dependencies named by the current CLI guide.
2. Run `java -jar dokka-cli-<VERSION>.jar -help` and nested `-sourceSet -help` before composing flags.
3. Supply `-pluginsClasspath`, `-sourceSet`, and `-outputDir` at minimum. The documented classpath/list separator is `;`.
4. Prefer one JSON configuration argument for repeatable nontrivial runs.
5. Add each output/plugin artifact and its dependencies at the exact Dokka version.

Minimal JSON shape:
```json
{
  "outputDir": "./build/dokka/html",
  "sourceSets": [{
    "sourceSetID": {"scopeId": "module", "sourceSetName": "main"},
    "sourceRoots": ["./src/main/kotlin"]
  }],
  "pluginsClasspath": ["./dokka-base.jar", "./analysis-kotlin-symbols.jar"]
}
```

Resolve real filenames and HTML dependencies from the live guide; never use placeholder jars in execution.
