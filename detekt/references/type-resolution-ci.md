# detekt type resolution/CI

## Task matrix

| project/task | type resolution |
|---|---|
| `detekt` | no |
| JVM `detektMain`, `detektTest` | yes |
| Android `detekt<Variant>` | yes |
| KMP `detekt<SourceSet>SourceSet` | no |
| KMP `detekt<Compilation><JvmOrAndroidTarget>` | yes |
| KMP Native/JS/Wasm source-set tasks | no |
| CLI | only correct classpath+JVM/compiler options/full mode |

Rules requiring full analysis are skipped without it. Mixed-behavior rules can report less in light mode. Coverage claim names exact task/mode.

Android configuration failure workaround `detekt.android.disabled=true` disables Android task creation; use only to isolate plugin integration, not as final Android coverage.

## Reports

Default Gradle outputs under `build/reports/detekt/`. Enable only consumed formats:
- HTML: human
- Checkstyle XML: CI parser
- SARIF: code scanning
- Markdown: human/review

Set `basePath` for relative paths in Checkstyle/SARIF. Verify report consumer accepts selected major's format ID.

Multi-module Checkstyle/SARIF merge requires Gradle >=7.4. Register release-matched `ReportMergeTask`; collect outputs from detekt tasks; run analysis+merge with `--continue` when findings would otherwise stop downstream merge.

## CI proof

1. clean run passes
2. seeded ordinary violation fails expected task
3. seeded type-aware violation fails type-resolution task but may not appear in light task
4. config error yields config failure, not zero findings
5. report exists, parses, paths map to repository
6. baseline hides only recorded debt; new finding still fails
7. `check` integration and cache/parallel behavior match intended policy

CLI exit: 0 clean; 1 unexpected; 2 findings; 3 invalid config.
