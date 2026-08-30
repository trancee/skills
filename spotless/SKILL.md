---
name: spotless
description: "Configures, applies, verifies, migrates, and troubleshoots Spotless formatting for Gradle and Maven projects. Use when adding Spotless, selecting and pinning formatter steps, defining targets and exclusions, enforcing formatting in CI, ratcheting legacy code, managing line endings or license headers, or diagnosing non-idempotent and formatter dependency failures. Don't use for direct ESLint, Prettier, or ktlint invocation, SBT integration, general lint-rule design, IDE-only formatting, or Spotless library development."
compatibility: "Current Gradle plugin 8.10.1 requires JRE 17+ and Gradle 8.1+; current Maven plugin 3.10.1 requires JRE 17+ and Maven 3.1+. Older runtimes require the documented legacy plugin line. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://github.com/diffplug/spotless"
  sourceVersion: "Gradle plugin 8.10.1@f2f2348ba1f28f84e7fa0d41373190478718d55e; Maven plugin 3.10.1@4ea1c6cbf46f4e60eb9e621406bf2621e28f2d68"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T13:56:22+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T13:56:22+02:00"
---

# Spotless

## Step 1: Establish scope and version

1. DEFINE install | formatter change | target change | ratchet adoption | CI enforcement | upgrade | failure diagnosis.
2. IDENTIFY Gradle or Maven, wrapper version, build JVM, modules, languages, generated/vendor directories, existing formatter files, CI command, and baseline state.
3. READ the current [Gradle guide](https://github.com/diffplug/spotless/tree/main/plugin-gradle) or [Maven guide](https://github.com/diffplug/spotless/tree/main/plugin-maven) plus its changelog before changing versions. Gradle and Maven plugin versions are independent.
4. PRESERVE existing formatter engines, formatter versions, target boundaries, step order, line-ending policy, and shared convention plugin unless the request changes them.
5. SELECT an older supported plugin line only when the build runtime cannot meet current requirements; record the compatibility reason.

Completion: exact integration, versions, modules, formats, targets, steps, and requested behavior are known.

## Step 2: Inspect configuration

RUN from the repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM every reported plugin declaration, version, format, formatter step, target/exclusion, ratchet ref, line-ending/encoding override, skip, error suppression, and CI task. Then list wrapper tasks or Maven effective configuration; treat unresolved aliases/properties as unresolved until traced.

Completion: helper evidence and build-tool-native configuration agree.

## Step 3: Define the formatting contract

1. DEFINE each format as ordered `target -> FormatterStep... -> canonical text`.
2. INCLUDE only owned source/configuration files. EXCLUDE generated output, build directories, vendored code, fixtures whose bytes are contractual, and external checkouts.
3. PIN external formatter versions when reproducible output matters. Keep their config files as the source of truth.
4. KEEP the default git-aware line-ending mode unless repository `.gitattributes` requires an explicit alternative; set encoding only from verified repository policy.
5. CHOOSE rollout: clean repository-wide formatting commit or `ratchetFrom` for incremental adoption.
6. DEFINE the enforcement command and whether CI checks the whole tree or the ratcheted delta.

Completion: every target and exclusion has ownership rationale; step order and rollout are explicit.

## Step 4: Configure the build integration

- Gradle -> READ `references/gradle.md` and apply its branch.
- Maven -> READ `references/maven.md` and apply its branch.
- Formatter choice or ordering -> READ `references/formatters.md`.
- Ratchet, line endings, lint, idempotence, or dependency failure -> READ `references/adoption-troubleshooting.md`.

Use the repository wrapper. Apply Spotless at the existing convention-plugin or owning-module seam; do not introduce a second configuration pattern.

Completion: the build resolves Spotless and exposes the intended check/apply tasks or goals.

## Step 5: Prove target and step behavior

1. ADD one deliberately misformatted owned file or line inside each new target.
2. RUN check; require failure naming that file.
3. RUN apply once; inspect the source diff for target boundaries and semantic preservation.
4. RUN apply again; require no new source diff. A second change exposes non-idempotent step composition.
5. RUN check; require success.
6. ADD or inspect one excluded/generated file; require no mutation and no check failure.
7. For lint-only steps, seed a matching violation; require the expected lint code/path, then fix it without broad suppression.

Completion: check is red before apply, apply is idempotent, check is green, and exclusions hold.

## Step 6: Adopt or migrate safely

1. CAPTURE the pre-apply worktree diff; formatting must not overwrite unrelated work.
2. For repository-wide adoption, isolate mechanical formatting from semantic changes.
3. For ratchet adoption, use a stable remote ref or tag such as `origin/main`, not `HEAD`; ensure CI fetches that ref with sufficient history.
4. For formatter/plugin upgrades, format a representative corpus and inspect output changes before repository-wide apply.
5. For custom steps, version their behavior so Gradle up-to-date checking and build cache invalidate when implementation changes.

Completion: the migration diff is reviewable and CI can resolve every ratchet/config dependency.

## Step 7: Wire enforcement

1. Gradle: retain the default `check -> spotlessCheck` dependency unless policy explicitly separates it; invoke the full task path in multi-project/composite builds.
2. Maven: bind `spotless:check` to `verify` through plugin execution and run `mvn verify`; do not bind `apply` to CI lifecycle.
3. Keep `apply` developer-controlled because it mutates sources.
4. Limit file-specific apply/check properties to local diagnosis; run the full enforcement command before completion.

Completion: the CI-equivalent command fails on a seeded violation and passes after apply/fix.

## Step 8: Diagnose failures

1. CLASSIFY configuration | target mismatch | formatter parse/lint | dependency/tool runtime | ratchet ref | encoding/line ending | non-idempotence.
2. REPRODUCE the narrow format-specific task/goal, then the aggregate check.
3. CORRECT source/configuration first. Use `targetExclude`, lint suppression, or ignore-error APIs only for a narrow documented exception.
4. If check still fails after apply, read `references/adoption-troubleshooting.md` and isolate the first non-idempotent FormatterStep.
5. If no files are formatted, inspect effective targets/exclusions and nested formatter config such as Biome/Prettier includes.

Completion: root cause is demonstrated by a failing command and removed by the fix.

## Step 9: Report completion

COPY `assets/integration-report.md` and fill exact versions, runtime, modules, targets, exclusions, ordered steps, rollout, commands, seeded-failure proof, idempotence proof, CI result, and limitations.

## Error Handling

- Current plugin cannot load -> align JRE/build-tool requirements or choose documented legacy line; never suppress class-version errors.
- `ratchetFrom` reference missing -> fetch the remote ref or remove shallow history; never silently switch to `HEAD`.
- Apply changes excluded files -> fix target/exclusion evaluation before accepting any formatting diff.
- Check fails after apply -> isolate step cycle/convergence and formatter config; do not loop apply blindly.
- Formatter executable/dependency missing -> verify pinned version, repository/proxy, Node/native executable, and config path for that step.
- Check unexpectedly passes -> verify plugin application, aggregate task path, Maven execution, skip flags, and target matches.
