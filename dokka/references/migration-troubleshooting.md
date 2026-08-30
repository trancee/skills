# Dokka migration and troubleshooting

## DGP v1 -> v2

DGP v2 is default since 2.1.0. Current migration minimums: Gradle 7.6, KGP 1.9, AGP 7.0.

Migration sequence:
1. Upgrade Dokka consistently.
2. Temporarily set `org.jetbrains.dokka.experimental.gradle.pluginMode=V2EnabledWithHelpers`.
3. Replace `tasks.withType<DokkaTask>`, `tasks.dokkaHtml`, `dokkaHtmlMultiModule`, and `DokkaCollectorTask` configuration with top-level `dokka {}`.
4. Move publication options to `dokkaPublications`; source/API options to `dokkaSourceSets`.
5. Replace `Visibility.PUBLIC` with `VisibilityModifier.Public`; replace `URL` source links with URI/string helpers.
6. Replace plugin JSON maps with typed `pluginsConfiguration`.
7. Replace implicit multi-project aggregation with `dokka(project(...))` dependencies.
8. Replace legacy tasks with `dokkaGenerate` or publication-specific tasks.
9. Account for full nested module paths; use `modulePath` only when preserving old URLs.
10. Remove GFM/Jekyll from DGP v2; use supported runner/plugin path only if explicitly required.
11. Run output comparison plus build/configuration-cache verification.
12. Set `org.jetbrains.dokka.experimental.gradle.pluginMode=V2Enabled`; remove all helpers.

## Failure diagnosis

- missing task: plugin applied in another module, wrong DGP mode, plugin alias unresolved, or legacy task name
- missing module: plugin absent from child or missing aggregator `dokka(project(...))`
- unresolved declaration/type: wrong inferred source roots, platform, classpath, or incompatible generated source registration
- unresolved external link: root URL lacks `/`, package-list discovery failed, network/offline mode, or target docs changed
- undocumented warning mismatch: `reportUndocumented` configured on wrong source set or visibility/package filters remove declaration
- duplicate page/key: conflicting module paths/names or analysis issue; minimize by module/source set before suppression
- OOM/metaspace: set `dokkaGeneratorIsolation = ProcessIsolation { maxHeapSize = "4g" }`, or test `ClassLoaderIsolation()` to share Gradle memory; measure both
- Android variants/flavors: confirm selected sources and current 2.2 limitations/issues before manual roots

Migration helpers preventing compilation errors are diagnostic scaffolding, not completion.
