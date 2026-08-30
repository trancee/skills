# Kover: [scope]

## Versions
- Kover/engine:
- Kotlin/Gradle|Maven/AGP/JDK:

## Scope
- modules/variants/JVM classes:
- test tasks:
- excluded targets/tests:

## Policy
- filters+rationale:
- unit/aggregation/group/bounds:
- instrumentation exclusions:

## Aggregation
- merger/Kover project dependencies:

## Proof
| task/scenario | expected | result/artifact |
|---|---|---|
| tests | pass | |
| seeded uncovered code | verify fail | |
| added meaningful test | verify pass | |
| report parse | intended classes | |

## Limits
- unmeasured target/test + reason:
