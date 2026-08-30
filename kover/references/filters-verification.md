# Kover filters/verification

## Filters

Report filters use fully qualified JVM class names, not file paths. Wildcards: `*`/`**` any chars; `?` one char. Excludes override includes.

Common filters apply all variants; total/named variant filters replace lower-priority filter set. Empty higher-level `filters {}` clears inherited filters.

Types: `classes`, `annotatedBy`, `inheritedFrom`, project filters where supported. Annotation filtering requires BINARY or RUNTIME retention. JaCoCo lacks some extended filters.

Source-set filters:
- `includedSourceSets`: only listed
- `excludedSourceSets`: wins includes
Test-task instrumentation: `disableForTestTasks`; excluded test is neither instrumented nor auto-run for report.

Instrumentation exclusion (`currentProject.instrumentation.excludedClasses`) prevents bytecode changes but project class remains with 0% coverage. Report exclusion removes class from report+verification. Choose intentionally.

## Verification model

Unit: `LINE` default | `INSTRUCTION` | `BRANCH`.
Aggregation: `COVERED_COUNT`, `MISSED_COUNT`, `COVERED_PERCENTAGE` default, `MISSED_PERCENTAGE`.
Grouping: `APPLICATION` default | `CLASS` | `PACKAGE`.

```kotlin
kover {
    reports {
        verify {
            rule("minimum line coverage") {
                minBound(80)
            }
        }
    }
}
```
Use `total.verify` only total; `variant("release").verify` only named variant; top-level `reports.verify` all variants.

Gate design:
1. measure stable intentional scope
2. exclude only generated/unowned/unmeasurable code with rationale
3. choose metric+group matching risk
4. set initial bound at/below observed value
5. seed uncovered code; verify task fails
6. add meaningful test; verify passes
7. ratchet upward through reviewed change

`warningInsteadOfFailure=true` converts verification failure to warning; use only explicit nonblocking policy.
