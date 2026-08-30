# Dokka content configuration

## Visibility and warnings

Default documented visibility is public. `reportUndocumented` emits warnings only after visibility/package/deprecation filters. `failOnWarning` turns any Dokka warning/error into build failure after reporting all messages. Pair them only when complete visible-API documentation is policy.

`suppressGeneratedFiles` defaults true for files under the build generated directory. `skipDeprecated`, `skipEmptyPackages`, `suppressInheritedMembers`, `suppressObviousFunctions`, `suppressAnnotatedWith`, and per-package regex rules change the published API surface; record each non-default as publication policy.

## Source links

Configure source links per source set:
- local directory: project-relative source root
- remote URL: durable repository path, preferably at published tag/commit
- line suffix: GitHub/GitLab `#L`; Bitbucket `#lines-`

DGP v2 uses URI/string helpers, not the legacy `URL` API.

## External documentation links

The root URL must end in `/`. Dokka attempts package-list discovery. Set `packageListUrl` when discovery fails or when using a cached local list. Kotlin stdlib, JDK, Android SDK, and AndroidX links are configured by default where applicable. `offlineMode=true` disables remote resolution and can leave dependency types unlinked.

## Module and package pages

Pass Markdown include files through publication/source-set `includes`. Their level-one headings are semantic:
```markdown
# Module exact-module-name

Module description.

# Package com.example.api

Package description.
```

Text until the next level-one `Module`/`Package` heading belongs to that entity. Validate names against generated module/package identities.

## Samples

Add sample roots to the relevant source set and reference resolvable functions with `@sample`. Compile/test sample source where possible; Dokka rendering alone does not prove sample validity. Since 2.2.0, samples render as non-runnable code blocks by default; interactive Kotlin Playground output requires its separate plugin.
