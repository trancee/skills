---
name: kotlin-binary-compatibility
description: "Configures, runs, migrates, and reviews Kotlin binary compatibility validation. Use when enabling Kotlin Gradle plugin ABI validation, maintaining ABI dumps, running checkKotlinAbi or updateKotlinAbi, using legacy apiCheck or apiDump, filtering public API, validating published artifacts, handling unsupported targets, or migrating from kotlinx binary-compatibility-validator. Don't use for source compatibility, runtime behavior testing, Java-only compatibility tools, semantic-version decisions without ABI review, or general Kotlin compilation."
compatibility: "Built-in ABI validation is experimental in Kotlin Gradle plugin 2.2.0+; verify the current Kotlin DSL before changes. Legacy binary-compatibility-validator 0.18.1 requires Gradle 6.1.1+ and Kotlin 1.6.20+, is in maintenance mode, and may require a pre-JDK-25 build runtime. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html"
  sourceVersion: "Kotlin 2.4.10 ABI validation docs (2026-04-28); binary-compatibility-validator 0.18.1@af4772c7cf1901fb0b824d4d5343353aa4eadcb7"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T14:24:21+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T14:24:21+02:00"
---

# Kotlin binary compatibility

## Step 1: Establish scope and validator

1. DEFINE enablement | ABI change review | baseline update | filter policy | multiplatform completeness | published-artifact validation | legacy migration | failure diagnosis.
2. IDENTIFY library modules, Kotlin/Gradle/AGP versions, JVM/Android/KLib targets, publications/transforms, current dump files, CI tasks, release compatibility policy, and supported build hosts.
3. READ the current [KGP ABI guide](https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html), KGP API reference, and legacy [validator repository](https://github.com/Kotlin/binary-compatibility-validator) before changing configuration.
4. SELECT the built-in Kotlin Gradle plugin validator for new adoption only when experimental DSL/dump stability is acceptable. PRESERVE the legacy plugin for existing builds unless migration is requested; it is maintained for fixes, not new features.
5. TREAT the validator as change detection. Classify each dump diff against compatibility policy; never infer semantic version or safety from task pass/fail alone.

Completion: validator, modules/targets, artifact boundary, baseline, host policy, and release policy are explicit.

## Step 2: Inspect configuration and dumps

RUN from the repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM built-in/legacy configuration, plugin/Kotlin versions, task names, filters, dump paths/files, publication source, KLib/unsupported-target settings, disabled validation, and modules. Then list Gradle wrapper tasks and resolve every version-catalog/convention-plugin indirection.

Completion: inspector evidence, Gradle task graph, and committed dump layout agree.

## Step 3: Define the ABI contract

1. DEFINE which published binaries and variants consumers link against.
2. DEFINE effectively public declarations, filters, annotations, generated API, and whether compatible additions require explicit baseline review.
3. DEFINE host completeness: inferred unsupported-target declarations or strict failure.
4. DEFINE whether compilation outputs or final Maven publications are authoritative.
5. DEFINE dump ownership, review approvers, CI check, and release-version response for accepted incompatibility.

Completion: every included/excluded declaration and target has a release-policy rationale.

## Step 4: Configure the selected validator

- Built-in KGP ABI validation -> READ `references/kgp-built-in.md`.
- Legacy `binary-compatibility-validator` -> READ `references/legacy-validator.md`.
- ABI diff classification -> READ `references/abi-review.md`.
- KMP hosts or transformed publications -> READ `references/multiplatform-publication.md`.
- Legacy-to-built-in cutover -> READ `references/migration.md`.

REUSE the repository's Kotlin plugin declaration, version catalog, convention plugin, and module ownership. Built-in validation is configured per module; legacy root application configures subprojects.

Completion: the chosen check/update tasks exist only for intended modules and are wired into `check`.

## Step 5: Establish or verify the baseline

1. If reference dumps exist, RUN the check task before edits and preserve its result.
2. If adopting validation, RUN the update/dump task once, then inspect the entire generated ABI as a public API review.
3. REMOVE accidental implementation/generated/internal declarations through source visibility or narrow filters; do not filter surprising API without understanding why it is public.
4. COMMIT reference dumps with the configuration that generated them.
5. RUN check again from a clean generated-output state.

Completion: checked-in dumps represent the intentionally supported binary API and check passes unchanged code.

## Step 6: Review an API change

1. RUN the check task; capture the exact dump diff.
2. MAP every changed line to its source declaration and published binary/target.
3. CLASSIFY removals and descriptor/access/inheritance changes with `references/abi-review.md`.
4. FIX unintended breakage in source. For intentional incompatible change, require the repository's version/deprecation/migration approval before baseline update.
5. For a compatible addition, still review exposure and opt-in status before accepting the dump.
6. RUN the update/dump task only after classification; inspect the resulting diff again.

Completion: every dump line is expected, classified, and tied to an approved source/API decision.

## Step 7: Configure filters safely

1. EXPRESS public API through source visibility first.
2. USE exclusions for effectively internal declarations that must remain JVM-public; use BINARY/RUNTIME-retained marker annotations where appropriate.
3. USE inclusions only for a deliberate allowlist; a declaration must pass all inclusion/exclusion logic.
4. SEED one excluded and one included declaration; verify exact dump membership.
5. REVIEW filter broadening as an API-policy change because it can hide breakage.

Completion: filter tests prove the exact public boundary without masking unrelated declarations.

## Step 8: Validate multiplatform and published artifacts

1. RUN checks on hosts that compile every supported target before release.
2. If unsupported-target inference is accepted, inspect inferred sections and refresh on a fully capable host. If completeness is mandatory, configure strict failure instead.
3. For post-processed JVM JARs, validate the final publication/artifact rather than pre-transform classes.
4. Keep platform dump identities and root project names stable.
5. Record Android/publication limitations before selecting Maven publications as the binary source.

Completion: each released target is validated from an authoritative host/artifact or explicitly marked unverified.

## Step 9: Migrate validators

1. READ `references/migration.md`; inventory legacy tasks, filters, dump directory, KLib settings, custom input JAR, CI, and consumers.
2. ADD built-in validation per intended module without deleting the legacy baseline.
3. GENERATE built-in dumps and compare public declarations/targets against legacy dumps.
4. PORT filters and host/publication policy; explain non-equivalent output.
5. SWITCH CI and `check` wiring only after seeded compatible/incompatible changes behave as expected.
6. REMOVE the legacy plugin/config/tasks and obsolete dumps in one clean cutover.

Completion: one validator and one authoritative dump set remain; CI detects the same intended breakages.

## Step 10: Verify and report

1. RUN unchanged check -> pass.
2. REMOVE or change the descriptor of one public member -> check fails with expected dump diff.
3. RESTORE it -> check passes.
4. ADD one intended public declaration -> check detects the addition; review and update; check passes.
5. VERIFY `check` invokes ABI validation and no disable/skip path bypasses CI.
6. VERIFY dumps are deterministic after a second update and contain only intended targets.
7. COPY `assets/validation-report.md`; fill exact validator/version/tasks/modules/dumps/filters/host/artifact source/diff classifications/results/limitations.

## Error Handling

- Check task missing -> verify Kotlin/legacy plugin application, module ownership, experimental opt-in, and full task path.
- Check passes after a seeded break -> inspect `enabled`/`validationDisabled`, `check` wiring, filters, target support, dump directory, and selected variant.
- Dump changes on unchanged source -> compare Kotlin/compiler/plugin/host/target/root-project versions before updating baseline.
- Update and check fail with Gradle implicit-dependency validation -> run update and check as separate Gradle invocations.
- Legacy validator reports `Unsupported class file major version 69` -> run Gradle with a supported runtime; JDK 21 is verified for 0.18.1.
- Unsupported Apple target differs by host -> regenerate on a capable host or select/document strict versus inferred policy.
- Published JAR differs from dump -> select Maven publications or the legacy task's final input JAR where supported.
- Migration produces unrelated churn -> keep both baselines, compare declaration-by-declaration, and delay cutover; never accept wholesale replacement without review.
