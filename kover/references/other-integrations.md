# Kover Maven/agent/CLI/offline

## Maven

Plugin `org.jetbrains.kotlinx:kover-maven-plugin:<VERSION>`; Maven>=3, Java>=8. Goals: `instrumentation`, `report-xml`, `report-html`, `report-ic`, `verify`, `log`. Wire executions to `verify` lifecycle.

Limits: only `test` goal instrumentation; integration-test goals unsupported. Several JVM agents can conflict; first Kover agent wins. Multi-module aggregate uses `<aggregate>true</aggregate>` plus dependencies. Excludes override includes. Keep all artifacts same version.

## JVM agent

Attach at JVM start:
```text
-javaagent:/path/kover-jvm-agent-VERSION.jar=file:/path/agent.args
```
Do not rename agent jar. Args file requires `report.file`; optional append/include/exclude regex/glob. Run tests/process to exit, then CLI converts IC report. Multiple instrumentation agents can be unstable.

## CLI

Commands:
- `instrument CLASS_ROOT... --dest DIR [filters] [--hits]`
- `report REPORT.ic... --classfiles ORIGINAL_ROOT... --src SRC... [--html DIR] [--xml FILE]`
- `merge REPORT.ic... --target MERGED.ic`

Reports require original non-instrumented class files and matching sources. Pin CLI/agent/runtime version.

## Offline

Use when Java agent unavailable:
1. compile originals
2. instrument copied class files
3. run copies with `kover-offline-runtime`
4. after tests finish, save/get report via shutdown property or runtime API
5. generate report using original classes

`kover.offline.report.path` overwrites existing file. `saveReport`/`getReport`/coverage collection only after measured code stops; concurrent collection is unpredictable. `getReport` bytes are standalone, not appendable.
