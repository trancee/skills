---
name: kotlin-api-reference
description: "Finds and verifies Kotlin API declarations across official Kotlin and kotlinx libraries and tools. Use when locating a symbol's canonical reference, matching API availability to dependency version and platform, resolving overload, extension, or expect-actual signatures, checking deprecation, opt-in, or Since metadata, tracing API docs to source, or comparing releases. Don't use for generating API documentation, general Kotlin implementation, third-party libraries outside the Kotlin ecosystem, Java-only APIs, or inferring runtime behavior from signatures alone."
compatibility: "Requires access to official Kotlin API portals or versioned source. API portals may document current releases and link moving master branches; verify against the project's exact dependency version. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/api-references.html"
  sourceVersion: "Kotlin API references; Kotlin Help build 1155 (2026-08-26)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T14:52:35+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T14:52:35+02:00"
---

# Kotlin API reference

## Step 1: Identify the exact API question

1. DEFINE lookup | availability | overload resolution | platform difference | opt-in/deprecation | behavior clarification | version comparison.
2. RECORD symbol spelling, expected fully qualified name, declaration kind, receiver, argument types, return context, library artifact/module, dependency version, Kotlin version, platform, and source set.
3. DISTINGUISH local/project API from external Kotlin ecosystem API. For local API, use language-server/source navigation; for generated API documentation, use the Dokka skill.
4. LIMIT this workflow to official Kotlin, kotlinx, Ktor, Kotlin Gradle plugin, Kotlin metadata, and Compose Material3 references listed by the official catalog.

Completion: one exact symbol/artifact/version/platform question is stated without relying on an unqualified name.

## Step 2: Inspect dependency evidence

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

For an isolated coordinate, add `--coordinate group:artifact:version`. CONFIRM detected literal/catalog/Maven coordinates, version resolution, Kotlin plugin/stdlib inference, API portal, and source repository. Resolve aliases, BOMs, constraints, parent properties, and dependency locking with the build tool before trusting a version.

Completion: the artifact and effective version used by the relevant source set are proven.

## Step 3: Select the authoritative reference

READ `references/catalog.md` to map the artifact family to its official API portal and source repository.

1. OPEN the library's official API root, then select the module/package before searching the symbol.
2. PREFER a declaration page over narrative guides, search snippets, or generated summaries.
3. If the portal exposes a version selector, select the project's exact version. If it exposes current docs only, mark the page provisional and continue to versioned source.
4. FOLLOW the declaration's source link, but inspect whether it targets a release tag/commit or moving `master`/`main`.

Completion: canonical declaration page and exact-version source candidate are identified.

## Step 4: Resolve the exact declaration

READ `references/declarations-platforms.md`.
If overload, platform, or moving-source ambiguity persists, READ `references/lookup-examples.md` and follow the matching case.

1. ENUMERATE every overload on the page; match receiver, parameter types/order/defaults, type parameters/bounds, return type, and modifiers.
2. CHECK whether the API is a member, extension, top-level declaration, constructor/factory, expect/actual declaration, or typealias.
3. CHECK platform/source-set labels for the matched overload, not only the page title.
4. RECORD `Since Kotlin`/library version, deprecation level/replacement, experimental/opt-in annotations, and platform constraints.
5. For extension ambiguity, prove imports and static receiver type in the caller.

Completion: one signature or a clearly enumerated overload set matches the calling context.

## Step 5: Verify version and source

READ `references/version-source-verification.md`.

1. COMPARE the dependency version with API-page version metadata and source-link ref.
2. When they differ or are absent, inspect the source at the dependency's release tag/commit and the release notes between versions.
3. CONFIRM declaration signature, annotations, platform source set, and implementation location in that ref.
4. For inline/const APIs, treat source body/value as consumer-relevant; signatures alone are insufficient.
5. Record unresolved version provenance explicitly; do not substitute latest behavior.

Completion: availability and contract are supported by exact-version documentation or source.

## Step 6: Verify behavior claims

1. SEPARATE documented contract from implementation detail.
2. USE source only to answer behavior left unspecified by the API contract; label implementation-dependent findings.
3. COMPILE a minimal probe against the project's actual dependency/target for overload resolution, opt-in, type inference, or platform availability.
4. RUN a focused behavioral probe/test only when the question concerns observable runtime behavior.
5. Avoid generalizing JVM behavior to common/JS/Native/Wasm or one actual implementation to all platforms.

Completion: each behavior claim is contract-backed or explicitly implementation-specific and exercised where needed.

## Step 7: Compare API versions

1. PIN both versions and the same artifact/module/platform.
2. COMPARE declaration signatures, source-set labels, annotations, Since/deprecation metadata, and source implementations.
3. READ release notes/migration guides for intentional changes.
4. DISTINGUISH absent API, renamed/moved API, overload addition, behavior change, and documentation-only change.
5. COMPILE the same probe against both versions when compatibility is material.

Completion: every stated version difference has evidence from both sides.

## Step 8: Report the answer

COPY `assets/api-evidence.md`; fill query, project coordinate/effective version, platform/source set, canonical page, matched signature, availability/annotations, source ref/path, behavior evidence, version comparison, and limitations.

CITE the declaration page and exact-version source/release notes. Quote only the minimum signature/contract needed.

## Error Handling

- Symbol search returns many pages -> qualify package/module/receiver and enumerate overloads before choosing.
- Page shows API but compilation fails -> verify effective artifact version, platform label, source set, imports, opt-in, and compiler/plugin version.
- Source link points to `master`/`main` -> reopen the same path at the dependency release tag; do not treat moving source as version proof.
- API portal has no version selector -> use exact-tag source and release notes; mark portal content current-only.
- Dependency version is managed by BOM/catalog/parent/lock -> query effective dependency graph; never infer from an alias name.
- Common API differs on platform -> inspect expect declaration and each relevant actual/platform overload.
- Runtime claim cannot be established from docs/source -> run a focused probe or state that behavior is unspecified.
