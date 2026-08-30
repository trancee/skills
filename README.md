# Agent Skills

Reusable skills for AI coding agents. Each skill packages a focused workflow, domain rules, primary references, and completion checks in a self-contained directory.

The repository uses the Agent Skills layout understood by Oh My Pi and compatible skill loaders. Each skill lives in a directory with a `SKILL.md` file. A skill can also include `assets/`, `references/`, and `scripts/`.

## Available skills

### Agent tooling

| Skill | Purpose |
| --- | --- |
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

### Oh My Pi: user-wide installation

Clone the repository somewhere stable:

```bash
git clone https://github.com/trancee/skills.git "$HOME/src/agent-skills"
mkdir -p "$HOME/.omp/agent/skills"
```

Install a skill by linking its complete directory into the user skill directory:

```bash
ln -s "$HOME/src/agent-skills/diataxis" \
  "$HOME/.omp/agent/skills/diataxis"
```

Repeat the link for each skill you want available. Linking instead of copying keeps relative `references/` and `resources/` intact and makes a later `git pull` immediately visible to the loader.

### Oh My Pi: project-local installation

To make a skill available only within one project, link or copy the complete skill directory under that project's `.omp/skills/` directory:

```bash
mkdir -p .omp/skills
ln -s "$HOME/src/agent-skills/nist-cavp" \
  .omp/skills/nist-cavp
```

Use an absolute symlink target so it remains valid regardless of the project's working directory. Commit a copied directory rather than a machine-specific symlink when the whole team needs the skill from the repository.

### Other agents

Use the skill directory configured by the agent or harness. Preserve the complete directory—not only `SKILL.md`—because a skill may load relative files at runtime.

Review a skill before installing it. Skills are instructions executed by an agent and can direct file, network, or command-line operations.

## Use

Skills with a `description` can be selected automatically when a request matches their scope. You can also invoke one explicitly by name:

```text
Use the nist-cavp skill to add AES-GCM vectors to this test suite.
```

The agent should read `SKILL.md` before acting, follow relative references from the skill directory, and satisfy the skill's completion checks. Explicit project instructions and user requirements still take precedence.

## Update

For linked installations:

```bash
cd "$HOME/src/agent-skills"
git pull --ff-only
```

Restart or reload the agent if its skill index is cached. Copied installations must be copied again or updated separately.

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

1. Create a lower-kebab-case directory containing `SKILL.md`.
2. Give the skill one focused responsibility and a precise discovery description.
3. Put the main procedure in `SKILL.md`. Move fixtures and templates to `assets/`, detailed guidance to `references/`, and executable helpers to `scripts/`.
4. Prefer primary, versioned sources. State which source wins when references disagree.
5. Keep secrets, credentials, generated output, and machine-specific paths out of the skill.
6. Exercise commands and behavioral procedures in an appropriate disposable environment.
7. Verify relative links, referenced files, and completion criteria before committing.
8. Use [Conventional Commits](https://www.conventionalcommits.org/) for repository history.

A useful contribution leaves no ambiguity about when the skill applies, what the agent must do, or how completion is verified.
