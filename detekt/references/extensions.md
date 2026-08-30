# detekt extensions/2.x migration

## Custom rules

- runtime discovery: `META-INF/services/dev.detekt.api.RuleSetProvider` containing provider FQCN (1.x uses legacy package)
- `detekt-api` dependency=`compileOnly`
- consume with `detektPlugins("<matching-coordinate>:<same-major-version>")`
- provider creates rule set; rule extends release-matched API
- tests: reporting and clean cases; `TestConfig`; type-aware rule uses release-matched analysis test utilities

2.x type-aware rules use Kotlin Analysis API marker/path, not K1 `BindingContext`. Use current [extension guide](https://detekt.dev/docs/introduction/extensions) and [migration guide](https://detekt.dev/docs/introduction/migration).

## 1.x -> 2.x map

- plugin `io.gitlab.arturbosch.detekt` -> `dev.detekt`
- Maven/package prefix -> `dev.detekt`
- formatting artifact -> `detekt-rules-ktlint-wrapper`
- rules modules renamed: comments, empty-blocks, potential-bugs; standard-library ruleset added
- task imports -> `dev.detekt.gradle.*`
- report IDs `xml`/`md` -> `checkstyle`/`markdown`; txt removed
- config removes `maxIssues`, weights, `excludeCorrectable`, `output-report`; severity now info/warning/error per YAML
- threshold keys mostly `allowed...`; YAML types strict
- some rule IDs renamed/split/removed; update config, baseline, suppressions
- 1.x baseline readable; regenerate only after migrated analysis passes and diff is reviewed
- compiler plugin removed
- custom API: `Issue`/`Debt` removed, `CodeSmell` -> `Finding`, provider returns factories, aliases annotation-based, Analysis API replaces `BindingContext`

Migration sequence:
1. pin baseline results on 1.x
2. update runtime tool tuple
3. change plugin/artifact/import coordinates
4. migrate config/report IDs/rule names
5. compile custom plugins/tests
6. run config validation, light+type-aware tasks
7. inspect findings/baseline/report diffs
8. switch CI only after equivalent/new policy proven
