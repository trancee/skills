---
name: detekt
description: "Configures, runs, migrates, and troubleshoots detekt static analysis for Kotlin projects. Use when adding the detekt Gradle plugin or CLI, selecting 1.x stable versus 2.x preview, configuring rules, baselines, suppressions, type resolution, reports, CI, auto-correction, or custom rule sets. Don't use for general Kotlin compilation, ktlint without detekt, Android Lint, or formatting tasks that do not use detekt."
compatibility: "Requires a Kotlin project and either its Gradle wrapper or a detekt CLI. detekt 2.x preview requires newer JDK/Kotlin/Gradle/AGP than 1.x; use the live compatibility table. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://detekt.dev/docs/intro"
  sourceVersion: "detekt docs 2.0.0-alpha.6; detekt/detekt@401c64bf232db0dcb054a7cfd0ca5fed3a095bc6; stable 1.23.8@046263730eb5368cb344489ac36543294e8e87bd"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T13:27:09+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T13:27:09+02:00"
---

# detekt

## 1. Scope+version

1. DEFINE install | config | findings | baseline | suppression | type resolution | report/CI | extension | 1.x->2.x migration.
2. INSPECT repository release policy, current plugin/CLI version, Kotlin/Gradle/AGP/JDK/JVM target, modules/source sets/variants, existing config/baselines/reports/plugins.
3. READ current [intro](https://detekt.dev/docs/intro), [changelog](https://detekt.dev/changelog), and [compatibility](https://detekt.dev/docs/introduction/compatibility) before version changes.
4. PRESERVE existing major unless migration requested. New project: 2.x only if prerelease policy accepts alpha; otherwise latest stable 1.x.
5. 1.x->2.x -> READ `references/migration-2.md` before edits.

## 2. Inspect

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```
CONFIRM plugin ID/version/module, `toolVersion`, config/baseline paths, rule plugins, Gradle options, reports, Kotlin project kind. Then list wrapper tasks; never guess variant/source-set names.

## 3. Establish policy

1. RUN existing detekt task and preserve exact findings/report/exit.
2. DEFINE source scope, rule sets, severity threshold, type-resolution requirement, CI report consumers, debt policy.
3. Resolve each finding in order: code fix -> rule config -> narrow justified `@Suppress` -> baseline only for accepted existing debt.
4. Never generate a baseline to hide newly introduced findings or regenerate it without reviewing removed/added IDs.
5. Auto-correct only after clean diff capture; never combine auto-correct with baseline generation/use.

## 4. Install/configure

READ `references/gradle-cli.md`.

- 2.x: plugin `dev.detekt`; artifacts/packages `dev.detekt`; current docs preview
- 1.x: plugin `io.gitlab.arturbosch.detekt`; matching legacy coordinates
- apply at owning module/convention-plugin level; preserve version catalog/build logic
- use wrapper; add `mavenCentral()` as required
- config file generated once, then keep only project overrides with `buildUponDefaultConfig=true` when desired
- validate config; correct YAML types; custom keys need validation exclusion
- avoid `allRules=true` absent explicit unstable-rule policy
- `failOnSeverity`/`ignoreFailures` must match CI gate; never disable failure merely to pass

## 5. Findings/baseline/suppression

READ `references/rules-baseline.md`.

- rule docs at exact detekt version define default activity, type-resolution need, properties
- config severity precedence: rule > ruleset > default `error`
- includes/excludes are rule/ruleset path filters; verify globs on real source paths
- suppression uses exact rule ID/alias and narrow declaration/file scope; explain false-positive or intentional exception
- baseline generation uses same task/config/plugins/classpath as enforcement
- source/variant-specific baseline overrides generic baseline for matching task

## 6. Type resolution

READ `references/type-resolution-ci.md`.

- plain `detekt` lacks type resolution
- JVM: `detektMain`/`detektTest`; Android: generated variant tasks
- KMP: source-set tasks lack type resolution; JVM/Android compilation tasks provide it; Native/JS/Wasm remain no-type-resolution
- CLI full analysis requires correct classpath, JVM target, language/API/JDK options
- rule marked full-analysis does not run in light mode; do not report clean coverage without required task

## 7. Extensions/migration

Custom rules -> READ `references/extensions.md`.

- extension versions/major coordinates match engine
- `detekt-api` is `compileOnly`; provider registered in `META-INF/services`
- test rule findings, clean cases, config, and type analysis when used
- 2.x migration includes plugin/group/package/module/rule/config/report renames and Analysis API transition; migrate config and baselines deliberately

## 8. Verify+report

1. RUN narrow owning task, then repository `check`/CI-equivalent.
2. REQUIRE expected failure on seeded violation and pass after fix/config; verify type-aware rule with type-aware task.
3. VERIFY reports at configured paths; SARIF/Checkstyle use stable relative paths (`basePath`). Multi-module merge uses supported task and `--continue` if findings must not block merge.
4. VERIFY baseline prevents old findings but fails a new seeded finding; inspect baseline diff.
5. Auto-correct path: inspect source diff; run detekt again; no baseline active.
6. OUT copy `assets/integration-report.md`; exact versions/tasks/config/findings/baseline/report/CI/limits.

## Fail

- plugin ID/coordinates mixed across majors => stop and choose one track
- unsupported tool tuple => align from live compatibility table
- config warning/error => fix schema/key/type; never suppress globally by default
- clean plain `detekt` but missing type-aware rules => run generated full-analysis task
- baseline path/task mismatch => regenerate only intended task with same config after review
- exit 1=unexpected error; 2=findings; 3=invalid config; diagnose accordingly
- custom plugin not loaded => check matching version, `detektPlugins`, service file, package/API major
