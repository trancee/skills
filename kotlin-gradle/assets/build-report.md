# Kotlin Gradle change: [scope]

## Version and ownership
- Gradle/KGP/AGP/daemon JDK:
- compile toolchains/targets:
- version/catalog/convention owner:
- selected KGP variant:

## Effective configuration
- modules/targets/source sets:
- compiler option levels/effective args:
- dependencies/configurations/repositories:
- generated-source producers:
- cache/daemon/report properties:

## Proof
| command/scenario | expected | observed |
|---|---|---|
| configuration/projects/tasks | model resolves | |
| narrow compile/test | passes | |
| JVM target/publication metadata | aligned | |
| repeated configuration-cache run | reused | |
| clean build-cache scenario | reused | |
| CI-equivalent check | passes | |

## Performance/diagnostics
- build report paths/findings:
- daemon/fallback evidence:

## Limitations
- unsupported tuple/host target/unverified path:
