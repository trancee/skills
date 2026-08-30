# Spotless Maven integration

Source: [Maven plugin guide](https://github.com/diffplug/spotless/tree/main/plugin-maven) and [changelog](https://github.com/diffplug/spotless/blob/main/plugin-maven/CHANGES.md).

Current 3.10.1 requires Maven 3.1+ running on JRE 17+. Use 2.46.1 for JRE 11 or 2.30.0 and older for JRE 8. Verify the live changelog before selecting a legacy line.

## Install

```xml
<plugin>
  <groupId>com.diffplug.spotless</groupId>
  <artifactId>spotless-maven-plugin</artifactId>
  <version>${spotless.version}</version>
  <configuration>
    <formats>
      <format>
        <includes>
          <include>*.md</include>
        </includes>
        <excludes>
          <exclude>target/**</exclude>
        </excludes>
        <trimTrailingWhitespace/>
        <endWithNewline/>
      </format>
    </formats>
    <java>
      <googleJavaFormat>
        <version>FORMATTER_VERSION</version>
      </googleJavaFormat>
    </java>
  </configuration>
  <executions>
    <execution>
      <goals><goal>check</goal></goals>
    </execution>
  </executions>
</plugin>
```

The `check` goal binds to `verify` when declared as an execution. Keep `apply` outside lifecycle bindings.

## Commands

- `./mvnw spotless:check`
- `./mvnw spotless:apply`
- `./mvnw verify`: includes declared Spotless check execution
- `./mvnw spotless:apply -DspotlessFiles='regex,...'`: diagnostic subset matched against absolute paths

Skip properties: `spotless.skip`, `spotless.check.skip`, `spotless.apply.skip`. A true property can make enforcement disappear; report every active property and CI override.

## Multi-module

Plugin management alone does not execute Spotless. Confirm the plugin is present in effective build plugins for every intended module. Parent configuration inheritance and child overrides define final formats; inspect `help:effective-pom` when ownership is unclear.

Maven up-to-date checking is enabled by default and stores its index under `target`; `mvn clean` removes it. A custom index path must remain disposable and module-safe.
