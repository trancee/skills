# Legacy validator to built-in KGP migration

The external plugin is in maintenance mode; built-in KGP ABI validation is experimental. Migration changes plugin ownership, task names, configuration scope, and dump format. Treat it as a reviewed tool migration, not a version bump.

## Mapping

| Legacy | Built-in KGP |
|---|---|
| root plugin `org.jetbrains.kotlinx.binary-compatibility-validator` | `kotlin { abiValidation { ... } }` in every intended module |
| `apiCheck` | `checkKotlinAbi` |
| `apiDump` | `updateKotlinAbi` |
| `ignoredProjects` | omit/disable validation in those modules |
| `ignoredPackages` / `ignoredClasses` | `filters.excluded.byNames` |
| `nonPublicMarkers` | `filters.excluded.annotatedWith` |
| `validationDisabled` | explicit built-in `enabled`/module policy; keep CI fail-closed |
| `apiDumpDirectory` | `referenceDumpDir` |
| KLib `strictValidation` | inverse policy via `keepLocallyUnsupportedTargets` |
| `apiBuild.inputJar` | `binariesSource`, usually `MAVEN_PUBLICATIONS` when supported |

Do not assume text dumps are identical. Built-in API also exposes legacy dump task providers for transition in some KGP versions; those APIs are experimental/deprecated across versions, so verify the exact KGP API before use.

## Cutover proof

1. Freeze source and run legacy `apiCheck`.
2. Add built-in validation alongside legacy without changing filters.
3. Generate both current representations.
4. Compare declaration sets per module/target, explaining format-only changes.
5. Seed a removal, descriptor change, compatible addition, filtered declaration, and unsupported-host case; require expected behavior from both.
6. Port publication input and CI task paths.
7. Remove external plugin/config and obsolete dump set together.
8. Run `check`, built-in ABI check, and a second update with no diff.

If built-in experimental behavior cannot reproduce a required legacy contract, keep the legacy plugin and document the blocker instead of narrowing coverage.
