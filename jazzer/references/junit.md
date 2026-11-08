# JUnit integration and build-tool execution

Sources: [released README](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/README.md), [example POM](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/examples/junit/pom.xml), [FuzzTest implementation](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/src/main/java/com/code_intelligence/jazzer/junit/FuzzTest.java), [configuration](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/docs/arguments-and-configuration-options.md).

## 1. Integrate as a test dependency

1. Inspect the existing JDK/toolchain, dependency catalog/BOM, Jupiter engine, test tasks and class naming conventions. Pin compatible Jazzer dependencies together; baseline here is 0.30.0, JUnit5.9+ upstream requirement. Do not publish Jazzer as a production dependency merely because README snippets use `implementation`.
2. Maven: add `com.code-intelligence:jazzer-junit:0.30.0` with test scope; retain an existing compatible `org.junit.jupiter:junit-jupiter` and JUnit Platform-capable Surefire configuration. The upstream example POM still pins Jazzer0.24.0; use the selected verified release, not its stale version.
   Import the project's compatible JUnit BOM to align Jupiter API/params/engine and Platform commons/launcher. Jazzer 0.30.0 brings transitive JUnit 5.9/Platform 1.9 artifacts; updating only the `junit-jupiter` aggregate can leave discovery broken (the probe hit missing `TempDirFactory`). The supplied POM uses BOM 5.11.4.
3. Gradle Kotlin DSL: add `testImplementation("com.code-intelligence:jazzer-junit:0.30.0")`, retain the compatible Jupiter dependency, and enable `useJUnitPlatform()` for the relevant JVM Test task. If the project uses a custom integration-test source set, place the dependency/target there deliberately. Kotlin Multiplatform recipes apply only to an actual JVM test target, not native/Android instrumentation tests.
4. Bazel: follow [rules_fuzzing Java setup](https://github.com/bazelbuild/rules_fuzzing#java-fuzzing) for native fuzzing targets or [the JUnit integration example](https://github.com/CodeIntelligenceTesting/example-bazel-junit) for explicit JUnit/corpus resource wiring. Do not transplant Maven corpus paths blindly into a Bazel sandbox.

## 2. Add one meaningful fuzz method

Annotate a concrete test method with `@FuzzTest`. It is a parameterized test and does not also need `@Test`. Place seed-source annotations such as `@MethodSource` before `@FuzzTest`; this release requires Jazzer's argument providers to run last and fails fuzz-mode startup otherwise, even if regression passed. Supported raw/provider/structured signatures and lifecycle choices are in `references/targets.md`.

For a complete disposable Maven consumer, copy `assets/pom.xml` to a new probe directory and `assets/SortFuzzTest.java` to `src/test/java/example/SortFuzzTest.java`. Create `src/test/resources/example/SortFuzzTestInputs/sortPreservesValues` before fuzzing so new findings have an intended destination. Keep the supplied seeds and invariant assertions; these probe library behavior, not the requested application's coverage.

## 3. Run regression and fuzzing separately

From the probe/project root:

```bash
# Regression on empty input, parameter-source seeds and saved findings.
mvn -Dtest=example.SortFuzzTest test
# A bounded new mutation campaign for exactly this fuzz method.
JAZZER_FUZZ=1 mvn '-Dtest=example.SortFuzzTest#sortPreservesValues' test
```

The probe annotation limits each fuzz campaign to 10s/10,000 executions. For a real target set an appropriate explicit budget; `@FuzzTest` defaults to five minutes and `maxExecutions=0` means no count bound. `jazzer.max_duration` and `jazzer.max_executions` override annotation values when passed through the actual test runner.

Gradle equivalent for an existing JVM test task:

```bash
./gradlew test --tests 'example.SortFuzzTest'
JAZZER_FUZZ=1 ./gradlew test --tests 'example.SortFuzzTest.sortPreservesValues' --rerun-tasks
```

- Unset `JAZZER_FUZZ` for regression. Use explicit `1` for fuzzing; do not rely on empty/nonempty interpretations in older Javadocs.
- Gradle up-to-date/cache state can skip a campaign. Use `--rerun-tasks` for manual fuzzing and disable caching/up-to-date reuse on a dedicated CI fuzz task where appropriate; do not globally invalidate unrelated test tasks.
- Verify JVM test-process environment and system properties. Gradle `-D` on its daemon is not automatic propagation to forked test workers; configure the relevant Test task's `environment`/`systemProperty`. Verify Maven runner forwarding against logs/configuration too.
- In fuzzing mode one fuzz method is executed and others are skipped. Select a method explicitly and inspect reports; suite success or skipped targets do not prove each target fuzzed. Run separate invocations/processes for separate fuzz targets.
- Regression runs are deterministic saved inputs, not new coverage-guided fuzzing. `JAZZER_COVERAGE=1` includes generated corpus entries in regression; it is not a claim of complete line coverage or a substitute for a new campaign.

## 4. Preserve corpus and regressions

- Generated coverage corpus: `.cifuzz-corpus/example.SortFuzzTest/sortPreservesValues`.
- Saved crash inputs: `src/test/resources/example/SortFuzzTestInputs/sortPreservesValues`; when this destination is absent, the working directory can receive the finding instead. Capture logs and inspect actual outputs rather than declaring a crash lost.
- Seeds from `@MethodSource`, `@ValueSource`, `@CsvSource` or `@ArgumentsSource` are regression cases and fuzzing seeds. Structured entries use Jazzer serialization; do not write literal JSON or text and assume the typed mutator will interpret it as an object.
- Retain reviewed fixed crashes in test resources under the same target contract. Keep corpus and resources as binary in narrow `.gitattributes` entries (`src/test/resources/example/SortFuzzTestInputs/** binary`, `.cifuzz-corpus/** binary` if versioned). Preserve originals before migration, avoid Git text normalization, and replay after signature/provider consumption changes.
- Check initialization warnings, reported input names and method-level tests. A seed ignored because it cannot serialize, a missing resource root or a skipped fuzz invocation is an evidence gap, not a pass.
- After a real defect fix, rerun the crash in regression mode and fuzz fresh. Security-hook findings may require instrumented replay; distinguish the exploit detector from the resulting application behavior.

DONE: selected method discovery, regression seeds, actual mutating fuzz execution, budget termination and saved-input replay are all evidenced for the intended target; Maven/Gradle/Bazel compatibility is claimed only where exercised.
