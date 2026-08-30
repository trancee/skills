# Agent Skills

Reusable skills for AI coding agents. Each skill packages a focused workflow, domain rules, primary references, and completion checks in a self-contained directory.

The repository uses the Agent Skills layout understood by Oh My Pi and compatible skill loaders. Each skill lives in a directory with a `SKILL.md` file. A skill can also include `assets/`, `references/`, and `scripts/`.

## Available skills

### Agent tooling

| Skill | Purpose |
| --- | --- |
| [`agent-skills-standard`](agent-skills-standard/) | Audit new and updated Agent Skills packages, gate skill repository commits, migrate catalogs, and add standards-compatible discovery and activation to agent clients. |
| [`omp-skill-hardener`](omp-skill-hardener/) | Mine repeated failures from OMP sessions, turn them into approved skill or `AGENTS.md` changes, and test the new rules. |

### Cryptography

| Skill | Purpose |
| --- | --- |
| [`nist-cavp`](nist-cavp/) | Find, download, parse, and integrate NIST CAVP archives and ACVP vector sets for cryptographic primitives and components. |
| [`ristretto255`](ristretto255/) | Implement, integrate, and review ristretto255, including canonical encoding, hash-to-group, scalars, constant-time operations, protocol use, and RFC vectors. |
| [`wycheproof`](wycheproof/) | Integrate and audit current Project Wycheproof vectors against cryptographic implementations, schemas, and result semantics. |

### Development

| Skill | Purpose |
| --- | --- |
| [`kotlin-development`](kotlin-development/) | Implement, review, build, test, and troubleshoot Kotlin projects across JVM, Android, Kotlin Multiplatform, JavaScript, Wasm, and Native. |
| [`xtool`](xtool/) | Install, configure, use, and troubleshoot xtool for SwiftPM-driven iOS development and device deployment. |

### Documentation

| Skill | Purpose |
| --- | --- |
| [`diataxis`](diataxis/) | Write, audit, and improve tutorials, how-to guides, reference, explanation, documentation architecture, and documentation quality. |

Open a skill's `SKILL.md` for its full procedure and source material.

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
8. Before committing skill repository changes, invoke `agent-skills-standard` again and run its strict package, metadata, link, discovery, and diff checks.
9. If the catalog changed, run `npx skills add . --list` and confirm that it exposes every intended skill.
10. Use [Conventional Commits](https://www.conventionalcommits.org/) for repository history.

A useful contribution leaves no ambiguity about when the skill applies, what the agent must do, or how completion is verified.
