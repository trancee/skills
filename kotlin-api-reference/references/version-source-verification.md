# Version and source verification

## Evidence order

1. effective resolved dependency for the relevant module/source set
2. exact-version official API page, when available
3. source at release tag/commit
4. release notes/migration guide between compared versions
5. minimal compile/runtime probe against the actual dependency

Current portal content alone cannot prove older-version availability.

## Read portal metadata

Capture module, package, signature, platform badges, Since, annotations, deprecation, samples, and source URL. Inspect the source URL ref:
- release tag/commit -> candidate exact-version evidence if it matches dependency
- `master`/`main` -> current moving implementation only
- different release family -> mismatch requiring exact-tag lookup

The stdlib portal can show many overloads with source links to a Kotlin release tag. kotlinx portals may link `master`; never equate that with the project's resolved version.

## Resolve versions

Gradle literal coordinates are only declarations. Version catalogs, BOM/platform constraints, dependency substitution, resolution rules, and lockfiles can change the selected version. Use the source set/module dependency report for the effective version.

For KGP APIs, match the Kotlin Gradle plugin version, not the stdlib version inferred from unrelated modules. For compiler-plugin-backed APIs such as serialization, verify runtime library and compiler plugin separately.

## Inspect source

Use the official repository file at the exact tag/commit. Confirm path/source set (`commonMain`, `jvmMain`, `jsMain`, `nativeMain`, generated source), signature, annotations, and body when behavior is material.

Generated source links are valid evidence but may point to generated files whose templates are elsewhere. Cite the generated declaration used by consumers.

## Compare versions

Use the same coordinate/module/platform and compare both refs. A symbol moving packages/modules can look removed. Overload additions can change source resolution without removing binary signatures. Inline body/const changes can affect already compiled consumers differently from ordinary calls.
