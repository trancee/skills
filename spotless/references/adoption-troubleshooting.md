# Spotless adoption and troubleshooting

## Ratchet

`ratchetFrom("origin/main")` / `<ratchetFrom>origin/main</ratchetFrom>` restricts formatting to files changed since a stable ref. Prefer a remote branch or tag. `HEAD` makes a misformatted commit immediately canonical. CI shallow clones must fetch the ref/history before check.

Choose one adoption strategy:
- whole tree: one isolated mechanical formatting change, then enforce all targets
- ratchet: enforce changed files now, move/refine the stable baseline deliberately

Do not mix a repository-wide apply with semantic edits.

## Line endings and encoding

Default `GIT_ATTRIBUTES_FAST_ALLSAME` follows Git and is recommended. Define repository line endings in `.gitattributes`; keep Git and Spotless policy aligned. Explicit encoding defaults to UTF-8 unless repository evidence says otherwise. An encoding safeguard failure means fix policy/input, not bypass safety.

## Idempotence

A valid formatter satisfies `F(F(input)) == F(input)`. Spotless padded-cell handling detects convergence/cycles and chooses canonical output; divergence stops after bounded attempts. If apply and check disagree:
1. run one format-specific apply
2. capture each successive result
3. remove steps from the end until stable
4. identify the first conflicting pair/config
5. fix or pin the formatter; keep narrow evidence if exclusion is unavoidable

## Lints and suppressions

Formatter steps can emit non-fixable lints. Fix source first. Gradle uses `suppressLintsFor`; Maven uses `lintSuppressions`. Match path, step, and short code narrowly. `ignoreErrorForStep`, `ignoreErrorForPath`, broad wildcards, `enforceCheck(false)`, and skip properties weaken enforcement; require explicit policy rationale.

## Dependency/tool failures

- npm steps: verify Node/npm version, package versions, lock/config paths, proxy, and parser selection
- Eclipse/P2: prefer versions with embedded lockfiles; verify cache directory/proxy and parallel resolution
- native command: verify executable path, permissions, stdin/stdout contract, version, and locale
- Java formatter: align build JVM, source syntax, and formatter version; Java 25 module imports require current supporting formatter
- Biome formats no files: check Biome config excludes and use a Spotless-specific config extending project config when needed

## Target mismatch

Inspect resolved targets, excludes, module ownership, source-set inference, generated directories, and case-sensitive paths. Android and Gradle-plugin Java sources need explicit Gradle targets. Maven generic formats and languages without conventional roots need explicit includes.
