# Spotless formatter selection and order

Spotless applies each FormatterStep sequentially. Order is contractual: a later step can undo an earlier step. Pin external formatter versions when output stability matters, and verify exact options against the current build-tool guide.

## Selection

- Java: choose one primary formatter (`googleJavaFormat`, `palantirJavaFormat`, `eclipse`, `princeOfSpace`, `idea`, or explicit alternative). Add import/refactoring/lint steps only for stated policy.
- Kotlin: choose `ktlint`, `ktfmt`, `diktat`, or project-standard formatter; keep `.editorconfig` authoritative where supported.
- Scala: use `scalafmt` and keep configured version consistent with `.scalafmt.conf`.
- JavaScript/TypeScript/JSON/CSS/Markdown: use project-standard Prettier, ESLint, Biome, Flexmark, or native format. Match parser/filepath and config discovery.
- Generic: define explicit targets before generic whitespace, regex, native command, license, or embedded-language steps.

Spotless Gradle and Maven support different matrix cells. Confirm the chosen formatter exists in the selected plugin guide instead of translating DSL mechanically.

## Order invariants

1. Run semantic refactoring steps such as `cleanthat` before the primary formatter.
2. Run `shortenFullyQualifiedTypes` before `importOrder`; inspect interaction with `removeUnusedImports` and the primary formatter.
3. Place indentation conversion after a formatter that always emits spaces when tabs are policy.
4. Place `licenseHeader` where later steps preserve its syntax and spacing.
5. Run generic newline normalization after content formatters only when repository policy requires it.
6. Prove `apply -> apply` produces no second diff for representative files.

## Reproducibility

Record Spotless plugin version, formatter engine/version, config file/version, runtime version, and native/Node executable version. Defaults can change between Spotless releases and across JVM versions; current google-java-format default differs by JVM level.

Native commands must read source on stdin and write only formatted source on stdout. Treat logs on stdout, nondeterminism, locale dependence, or network dependence as formatter defects.

Formatter parse failures are not target exclusions by default. Fix invalid source/config, or add a narrow documented exclusion only when bytes are intentionally outside the contract.
