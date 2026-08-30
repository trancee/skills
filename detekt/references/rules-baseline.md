# detekt rules/baseline

## Finding disposition

For each finding:
1. fix code if rule matches policy
2. tune rule/property/path if project policy differs
3. narrow `@Suppress` for documented false positive/intentional exception
4. baseline only accepted pre-existing debt

No blanket suppression, disabled failure gate, or baseline refresh solely for green CI.

## Config

Exact-version rule docs define rule set ID, rule ID, default activation, properties, aliases, type-resolution requirement.

```yaml
config:
  validation: true
  warningsAsErrors: true
complexity:
  severity: warning
  TooManyFunctions:
    severity: error
    thresholdInFiles: 20
    excludes: ['**/generated/**']
```
Severity: rule > ruleset > default error. Verify YAML names/types against selected version; 2.x migration renames many threshold keys to `allowed...`.

## Suppression

Kotlin: `@Suppress("LongMethod")`, optional `detekt:` or ruleset prefix; aliases allowed. Kotlin `@Suppress` wins when Java `@SuppressWarnings` also present.
Use smallest declaration/file scope; exact rule ID; comment/rationale per repo convention. Suppression is reviewed policy, not automatic fix.

## Baseline

Baseline XML IDs: `<RuleID>:<FindingSignature>`. `CurrentIssues`=generated debt; `ManuallySuppressedIssues`=explicit false positives.

Create with same analysis path used in CI:
```bash
./gradlew detektBaseline
./gradlew detektBaselineMain
./gradlew detektBaseline<Variant>
```
Specific baseline (for example `detekt-main.xml`) takes precedence over generic `detekt.xml` for matching task.

Before accept:
- same config/rule plugins/source/classpath/JVM target as enforcement
- inspect added+removed IDs
- confirm only old accepted findings
- seed new violation; enforcement must fail
- auto-correct absent; detekt docs state baseline and auto-format cannot combine safely

When code fixes remove findings, prune baseline via deliberate regeneration/diff. Never hand-edit opaque signatures unless exact rule/signature understood.
