# Agent Skills

Reusable skills for AI coding agents. Each skill packages a focused workflow, domain rules, primary references, and completion checks in a self-contained directory.

The repository uses the Agent Skills layout understood by Oh My Pi and compatible skill loaders: a directory containing a `SKILL.md` file with YAML frontmatter. Some skills include additional material under `references/` or `resources/`.

## Available skills

| Skill | Purpose |
| --- | --- |
| [`diataxis`](diataxis/) | Write, audit, and improve tutorials, how-to guides, reference, explanation, documentation architecture, and documentation quality. |
| [`nist-cavp-test-vectors`](nist-cavp-test-vectors/) | Find, download, parse, and integrate NIST CAVP or ACVP test vectors for cryptographic algorithms and primitive components. |
| [`ristretto255`](ristretto255/) | Implement, integrate, and review ristretto255, including canonical encoding, hash-to-group, scalars, constant-time operations, protocol use, and RFC vectors. |
| [`wycheproof`](wycheproof/) | Integrate and audit current Project Wycheproof vectors against cryptographic implementations, schemas, and result semantics. |
| [`xtool-ios-development`](xtool-ios-development/) | Install, configure, troubleshoot, and use xtool for SwiftPM-driven iOS development on Linux, WSL, or macOS. |

Open a skill's `SKILL.md` for its full procedure and source material.

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
ln -s "$HOME/src/agent-skills/nist-cavp-test-vectors" \
  .omp/skills/nist-cavp-test-vectors
```

Use an absolute symlink target so it remains valid regardless of the project's working directory. Commit a copied directory rather than a machine-specific symlink when the whole team needs the skill from the repository.

### Other agents

Use the skill directory configured by the agent or harness. Preserve the complete directory—not only `SKILL.md`—because a skill may load relative files at runtime.

Review a skill before installing it. Skills are instructions executed by an agent and can direct file, network, or command-line operations.

## Use

Skills with a `description` can be selected automatically when a request matches their scope. You can also invoke one explicitly by name:

```text
Use the nist-cavp-test-vectors skill to add AES-GCM vectors to this test suite.
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
│   ├── references/    # optional detailed guidance
│   └── resources/     # optional supporting material
└── ...
```

A skill's frontmatter provides its discovery contract:

```yaml
---
name: example-skill
description: Perform a specific workflow when its triggering conditions apply.
metadata:
  source: "https://example.com/canonical-source"
  createdAt: "2026-01-01T12:00:00+00:00"
  updatedAt: "2026-01-02T12:00:00+00:00"
---
```

- `name` matches the lower-kebab-case directory name.
- `description` states what the skill does and the distinct situations that should trigger it.
- `metadata.source` identifies the canonical source used to author and refresh the skill.
- `metadata.createdAt` records the skill's first repository creation time as an ISO 8601 string.
- `metadata.updatedAt` records the latest skill content or metadata update as an ISO 8601 string.
- The body contains ordered actions, decision points, constraints, and checkable completion criteria.
- Relative links resolve from the skill directory.

## Contributing

1. Create a lower-kebab-case directory containing `SKILL.md`.
2. Give the skill one focused responsibility and a precise discovery description.
3. Put universal steps in `SKILL.md`; move branch-specific detail into `references/` or `resources/` when that keeps the main procedure legible.
4. Prefer primary, versioned sources. State which source wins when references disagree.
5. Keep secrets, credentials, generated output, and machine-specific paths out of the skill.
6. Exercise commands and behavioral procedures in an appropriate disposable environment.
7. Verify relative links, referenced files, and completion criteria before committing.
8. Use [Conventional Commits](https://www.conventionalcommits.org/) for repository history.

A useful contribution leaves no ambiguity about when the skill applies, what the agent must do, or how completion is verified.
