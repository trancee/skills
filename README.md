# Agent Skills

Reusable skills for AI coding agents. Each skill packages a focused workflow, domain rules, primary references, and completion checks in a self-contained directory.

The repository uses the Agent Skills layout understood by Oh My Pi and compatible skill loaders. Each skill lives in a directory with a `SKILL.md` file. A skill can also include `assets/`, `references/`, and `scripts/`.

## Available skills

### Agent tooling

| Skill | Context tokens | Purpose |
| --- | ---: | --- |
| [`agent-skills-standard`](agent-skills-standard/) | 2,880 | Audit new and updated Agent Skills packages, gate skill repository commits, migrate catalogs, and add standards-compatible discovery and activation to agent clients. |
| [`omp-skill-hardener`](omp-skill-hardener/) | 2,412 | Mine repeated failures from OMP sessions, turn them into approved skill or `AGENTS.md` changes, and test the new rules. |

### Cryptography

| Skill | Context tokens | Purpose |
| --- | ---: | --- |
| [`nist-cavp`](nist-cavp/) | 2,729 | Find, download, parse, and integrate NIST CAVP archives and ACVP vector sets for cryptographic primitives and components. |
| [`ristretto255`](ristretto255/) | 2,790 | Implement, integrate, and review ristretto255, including canonical encoding, hash-to-group, scalars, constant-time operations, protocol use, and RFC vectors. |
| [`wycheproof`](wycheproof/) | 2,060 | Integrate and audit current Project Wycheproof vectors against cryptographic implementations, schemas, and result semantics. |

### Development

| Skill | Context tokens | Purpose |
| --- | ---: | --- |
| [`detekt`](detekt/) | 3,556 | Configure, run, migrate, and troubleshoot detekt static analysis for Kotlin projects. |
| [`kover`](kover/) | 3,182 | Configure, verify, aggregate, and troubleshoot Kotlinx Kover JVM coverage for Kotlin projects. |
| [`kotlin-api-reference`](kotlin-api-reference/) | 3,279 | Find and verify versioned, platform-specific Kotlin ecosystem API declarations and source. |
| [`kotlin-binary-compatibility`](kotlin-binary-compatibility/) | 4,351 | Configure, run, migrate, and review Kotlin ABI validation with built-in KGP or the legacy validator. |
| [`kotlin-coroutines`](kotlin-coroutines/) | 4,709 | Design, implement, test, and troubleshoot Kotlin coroutines, Flow, channels, cancellation, and structured concurrency. |
| [`kotlin-development`](kotlin-development/) | 3,245 | Implement, review, build, test, and troubleshoot Kotlin projects across JVM, Android, Kotlin Multiplatform, JavaScript, Wasm, and Native. |
| [`kotlin-gradle`](kotlin-gradle/) | 4,366 | Configure, migrate, optimize, and troubleshoot Kotlin Gradle builds, toolchains, compiler options, and caches. |
| [`kotlin-multiplatform`](kotlin-multiplatform/) | 4,276 | Design, configure, migrate, test, publish, and troubleshoot Kotlin Multiplatform targets, source sets, hierarchies, and variants. |
| [`kotlin-native-apple-interop`](kotlin-native-apple-interop/) | 4,644 | Configure, export, import, and troubleshoot Kotlin/Native interoperability with Swift, Objective-C, and Apple frameworks. |
| [`kotlin-power-assert`](kotlin-power-assert/) | 3,850 | Configure, use, debug, and expose Kotlin Power-assert diagnostics, transformed functions, and assertion APIs. |
| [`kotlinx-benchmark`](kotlinx-benchmark/) | 4,430 | Configure, run, compare, and troubleshoot multiplatform Kotlin microbenchmarks with kotlinx-benchmark. |
| [`kotlinx-serialization`](kotlinx-serialization/) | 4,613 | Design, configure, evolve, test, and troubleshoot kotlinx.serialization wire formats and schemas. |
| [`lincheck`](lincheck/) | 3,787 | Design, run, interpret, and troubleshoot JVM concurrency tests with Lincheck model checking and stress strategies. |
| [`skie`](skie/) | 3,315 | Install, migrate, configure, and troubleshoot Touchlab SKIE for Kotlin Multiplatform Swift interop. |
| [`spotless`](spotless/) | 3,947 | Configure, apply, verify, migrate, and troubleshoot Spotless formatting for Gradle and Maven projects. |
| [`xtool`](xtool/) | 2,285 | Install, configure, use, and troubleshoot xtool for SwiftPM-driven iOS development and device deployment. |

### Documentation

| Skill | Context tokens | Purpose |
| --- | ---: | --- |
| [`diataxis`](diataxis/) | 2,693 | Write, audit, and improve tutorials, how-to guides, reference, explanation, documentation architecture, and documentation quality. |
| [`dokka`](dokka/) | 4,486 | Configure, generate, publish, migrate, and troubleshoot Dokka API documentation for Kotlin and mixed Java projects. |

Open a skill's `SKILL.md` for its full procedure and source material.

Context tokens use `tiktoken>=0.14` with the GPT-5.6-compatible `o200k_base` encoding. Each value is the sum of `SKILL.md` and direct files under `assets/` and `references/`; scripts and license files are excluded. Resources load only when needed, so the table is a packaged-context upper bound rather than the cost of every activation.

Regenerate the table values from the repository root:

```bash
python3 agent-skills-standard/scripts/count-context.py --root .
```

Categories are catalog metadata. They do not affect skill invocation, and skill directories remain at the repository root.

## Install

The [skills CLI](https://github.com/vercel-labs/skills) requires Node.js and `npx`.

List the skills in this repository before installing them:

```bash
npx skills add trancee/skills --list
```

Install skills for the current project:

```bash
npx skills add trancee/skills
```

The CLI detects supported agents and prompts you to choose the skills and target agents. Project installation is the default.

To install one skill, pass its name:

```bash
npx skills add trancee/skills --skill kotlin-development
```

To make the selected skills available across projects, use global scope:

```bash
npx skills add trancee/skills --global
```

Review each skill before installing it. Skills can direct an agent to edit files, run commands, or access the network.

## Use

Skills with a `description` can be selected automatically when a request matches their scope. You can also invoke one explicitly by name:

```text
Use the nist-cavp skill to add AES-GCM vectors to this test suite.
```

The agent should read `SKILL.md` before acting, follow relative references from the skill directory, and satisfy the skill's completion checks. Explicit project instructions and user requirements still take precedence.

## Update

Update installed skills and choose the scope when prompted:

```bash
npx skills update
```

Select project scope, global scope, or one named skill directly:

```bash
npx skills update --project
npx skills update --global
npx skills update kotlin-development
```

## Repository layout

```text
skills/
├── README.md
├── <skill-name>/
│   ├── SKILL.md
│   ├── assets/        # optional fixtures and templates
│   ├── references/    # optional detailed guidance
│   └── scripts/       # optional executable helpers
└── ...
```

A skill's frontmatter provides its discovery contract:

```yaml
---
name: example-skill
description: Perform a specific workflow when its triggering conditions apply.
metadata:
  category: "development"
  source: "https://example.com/canonical-source"
  sourceVersion: "upstream release, document, page revision, or commit"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-01-01T12:00:00+00:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-01-02T12:00:00+00:00"
---
```

- `name` matches the lower-kebab-case directory name.
- `description` states what the skill does and the distinct situations that should trigger it.
- `metadata.category` groups the skill under `agent-tooling`, `cryptography`, `development`, or `documentation` in this repository.
- `metadata.source` identifies the canonical source used to author and refresh the skill.
- `metadata.sourceVersion` records the upstream release, document identifier, dated page revision, or commit used to author or refresh the skill.
- `metadata.createdBy` records the `provider/model` identifier that first created the skill.
- `metadata.createdAt` records the skill's first repository creation time as an ISO 8601 string.
- `metadata.updatedBy` records the `provider/model` identifier that made the latest content or metadata change.
- `metadata.updatedAt` records the latest skill content or metadata update as an ISO 8601 string.
- The body contains ordered actions, decision points, constraints, and checkable completion criteria.
- Relative links resolve from the skill directory.

## Contributing

Write for the consumer. Keep `SKILL.md`, agent-facing references, and agent-filled templates terse. Use stable labels, fragments, symbols, and exact commands when they preserve meaning. Remove connective prose. Write human-facing documentation, including this README, in clear natural English.

1. Use `skill-creator` to create a skill or revise its procedure.
2. Run `agent-skills-standard` on every new or updated package before calling the package complete.
3. Give the skill one focused responsibility and a precise discovery description.
4. Put the main procedure in `SKILL.md`. Move fixtures and templates to `assets/`, detailed guidance to `references/`, and executable helpers to `scripts/`.
5. Prefer primary, versioned sources. State which source wins when references disagree.
6. Keep secrets, credentials, generated output, and machine-specific paths out of the skill.
7. Exercise commands and behavioral procedures in an appropriate disposable environment.
8. After any `SKILL.md`, direct `references/*`, or direct `assets/*` change, run `python3 agent-skills-standard/scripts/count-context.py --root . --baseline HEAD path/to/skill`. Record the `o200k_base` core, resource, total, baseline, and delta counts.
9. Before committing skill repository changes, invoke `agent-skills-standard` again. Re-run its strict audit and token count against the final files, then run metadata, link, discovery, and diff checks.
10. If the catalog changed, run `npx skills add . --list` and confirm that it exposes every intended skill.
11. Use [Conventional Commits](https://www.conventionalcommits.org/) for repository history.

A useful contribution leaves no ambiguity about when the skill applies, what the agent must do, or how completion is verified.
