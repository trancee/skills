---
name: dokka
description: "Configures, generates, publishes, migrates, and troubleshoots Dokka API documentation for Kotlin and mixed Kotlin/Java projects. Use when adding Dokka to Gradle, Maven, or CLI builds; configuring source sets, visibility, links, samples, module or package documentation, HTML or Javadoc output, multi-project aggregation, javadoc JARs, plugins, or DGP v1-to-v2 migration. Don't use for general prose documentation, KDoc style review without Dokka generation, Java's javadoc tool alone, or developing Dokka itself."
compatibility: "Current Dokka 2.2.0 Gradle plugin requires Gradle 7.6+, Kotlin Gradle plugin 1.9+, and Android Gradle plugin 7.0+ where applicable. Maven and CLI paths require a Java runtime. Helper requires Python 3.11+."
metadata:
  category: "documentation"
  source: "https://kotlinlang.org/docs/dokka-introduction.html"
  sourceVersion: "Dokka 2.2.0 (Kotlin/dokka@656ca46fbbd676d872b0bd383042fc12ae7adcdd)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T14:08:32+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T14:08:32+02:00"
---

# Dokka

## Step 1: Establish scope and version

1. DEFINE install | source-set configuration | content/link policy | output customization | aggregation | publication | plugin | DGP v1-to-v2 migration | failure diagnosis.
2. IDENTIFY Gradle, Maven, or CLI; Kotlin/Java/Android/KMP project type; build versions; modules/source sets; public API boundary; existing Dokka mode/configuration/tasks; output consumer.
3. READ the current [Dokka introduction](https://kotlinlang.org/docs/dokka-introduction.html), selected runner guide, and [latest release](https://github.com/Kotlin/dokka/releases/latest) before changing versions.
4. KEEP every `org.jetbrains.dokka` artifact/plugin at one verified version. Treat HTML as recommended; treat Javadoc, GFM, and Jekyll stability limits explicitly.
5. USE DGP v2 for new Gradle integrations. DGP v2 and K2 analysis are default since 2.1.0.

Completion: runner, version, mode, source sets, output formats, aggregation boundary, and publication consumer are explicit.

## Step 2: Inspect configuration

RUN from the repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM plugin IDs/versions, legacy DGP v1 APIs, migration flags, Dokka dependencies/plugins, aggregation edges, source-set options, warning policy, output paths, runner goals/tasks, and CLI configuration. Then query build-tool-native tasks/effective configuration; resolve every alias/property before editing.

Completion: helper evidence and effective build configuration agree.

## Step 3: Define the API-documentation contract

1. DEFINE documented modules/source sets/platforms and visibility boundary.
2. DEFINE required KDoc/Javadoc coverage, warning policy, deprecated/generated/inherited-member policy, package exclusions, samples, source links, and external links.
3. DEFINE output format, output directory, branding/assets, multi-project navigation, archive classifier, and publishing task.
4. PIN source links to the published source revision when durable links matter.
5. KEEP inferred source roots/classpaths unless generation proves inference wrong; manual roots/classpaths can silently omit platform sources.

Completion: every documented and suppressed scope has a rationale; output and CI acceptance are checkable.

## Step 4: Configure the runner

- Gradle/DGP v2 -> READ `references/gradle-v2.md`.
- Maven or CLI -> READ `references/maven-cli.md`.
- source sets, links, samples, module/package pages, visibility, warnings -> READ `references/content-configuration.md`.
- DGP v1 migration or generation failure -> READ `references/migration-troubleshooting.md`.
- output formats, customization, archives, publication -> READ `references/output-publishing.md`.

REUSE the repository's version catalog, convention plugin, wrapper, Maven parent, and publication pattern. Introduce no parallel configuration seam.

Completion: the intended runner exposes the exact generation task/goal and resolves all Dokka plugins.

## Step 5: Configure content and links

1. CONFIGURE shared module settings at top-level, format/output settings in `dokkaPublications`, and platform/API inputs in `dokkaSourceSets`.
2. PAIR `reportUndocumented=true` with `failOnWarning=true` only when undocumented public API must gate CI; otherwise record warnings as advisory.
3. VALIDATE each source-link local root against its remote URL and line suffix.
4. END every external documentation root URL with `/`; supply a local/remote package list when automatic discovery fails.
5. VALIDATE each include file uses exact `# Module <name>` and `# Package <qualified.name>` headings.
6. COMPILE or otherwise validate every `@sample` target; Dokka 2.2 renders samples as non-runnable blocks unless the playground plugin is added.

Completion: declarations, links, samples, and include files resolve in generated output.

## Step 6: Aggregate multi-project documentation

1. APPLY Dokka to every documentable subproject.
2. SHARE configuration through the existing convention plugin; avoid new `subprojects {}`/`allprojects {}` cross-project configuration in DGP v2.
3. DECLARE every aggregation edge in the aggregator:
   ```kotlin
   dependencies {
       dokka(project(":library"))
   }
   ```
4. CHECK generated module paths. DGP v2 preserves the full project path; set `modulePath` only for an intentional compatibility URL.
5. GENERATE from the aggregator's full Gradle task path.

Completion: every intended module appears once and every inter-module link resolves.

## Step 7: Generate and inspect output

1. RUN the narrow generation task/goal, then the publication/CI task.
2. OPEN generated entry pages and inspect navigation, signatures, source-set tabs, KDoc/Javadoc, samples, package/module pages, source links, external links, assets, and footer.
3. SEARCH generation output for unresolved links, warnings, duplicate pages, empty modules, and missing source sets.
4. SEED one undocumented visible declaration when warnings gate CI; require failure, document/fix it, then require success.
5. RE-RUN without source/config changes; require the Gradle task to become up-to-date/from cache where supported.

Completion: output is consumable, warnings match policy, and repeated generation is stable.

## Step 8: Package and publish

1. CONSUME `dokkaGeneratePublicationHtml` when another Gradle task needs the declared HTML output directory; use `dokkaGenerate` for normal all-format generation.
2. ATTACH the documentation archive through the repository's existing Maven/Gradle publication model; do not replace source artifacts.
3. VERIFY archive contents include the generated entry point and exclude transient caches.
4. PUBLISH to a disposable/local destination first; resolve the produced classifier and inspect repository metadata.
5. KEEP experimental Maven Javadoc goals and Alpha output formats behind explicit acceptance.

Completion: the local publication contains the intended documentation artifact and links to its source revision.

## Step 9: Migrate DGP v1 to v2

1. READ `references/migration-troubleshooting.md` and enable `V2EnabledWithHelpers` only during migration.
2. MOVE task-based configuration to top-level `dokka {}` DSL, JSON plugin configuration to typed `pluginsConfiguration`, and implicit multi-module tasks to `dokka(project(...))` dependencies.
3. REPLACE legacy `dokkaHtml`/`dokkaHtmlMultiModule` consumers with publication tasks and account for changed module paths.
4. REMOVE unsupported DGP v2 Markdown/Jekyll assumptions.
5. RUN generation plus build/configuration-cache checks.
6. REPLACE helpers with `V2Enabled` after every legacy API is removed.

Completion: no DGP v1 API/helper remains and the output contract is preserved or intentionally migrated.

## Step 10: Report completion

COPY `assets/integration-report.md`; fill exact versions, runner/mode, modules/source sets, visibility/content policy, formats/tasks, plugins, links, warning proof, output inspection, publication artifact, migration changes, and limitations.

## Error Handling

- Plugin/task missing -> verify plugin application, DGP mode, module ownership, version catalog, and full task path.
- Undocumented warnings do not fail -> verify both `reportUndocumented` and publication `failOnWarning` at the effective scope.
- Types/links unresolved -> inspect inferred classpath/source roots/platform, external package list, trailing slash, and offline mode before manual overrides.
- Multi-project output incomplete -> verify Dokka applies to each child and every `dokka(project(...))` edge exists.
- Out of memory -> tune `ProcessIsolation.maxHeapSize` or test `ClassLoaderIsolation`; measure Gradle plus generator memory.
- DGP v1 symbols compile under helpers -> finish migration; helpers mask removed APIs and are not the final state.
- CLI fails to start -> align every Dokka/plugin dependency version and inspect `-help`; classpath entries use the documented semicolon separator.
