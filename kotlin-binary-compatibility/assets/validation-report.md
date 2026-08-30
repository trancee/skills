# Kotlin ABI validation: [scope]

## Toolchain
- validator/version:
- Kotlin/Gradle/AGP:
- modules/targets/hosts:

## ABI contract
- authoritative binaries/publications:
- reference dump paths/formats:
- filters/markers+rationale:
- unsupported-target policy:
- CI/check wiring:

## Diff review
| declaration/dump line | target | change | compatibility classification | decision |
|---|---|---|---|---|
| | | | | |

## Proof
| scenario | expected | observed |
|---|---|---|
| unchanged source | check passes | |
| removed/descriptor-changed API | check fails | |
| restored API | check passes | |
| compatible addition | detected, reviewed, accepted | |
| repeated update | no dump diff | |
| unsupported host/publication | policy enforced | |

## Migration and limitations
- legacy-to-built-in mapping/results:
- unverified target/artifact/compatibility dimension:
