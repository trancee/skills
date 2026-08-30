# Agent Skills package spec

REFRESH: [live spec](https://agentskills.io/specification).

## Layout

`<package>/SKILL.md` required; case-sensitive. Optional: `scripts/`, `references/`, `assets/`, other resources. `SKILL.md` = `---` YAML `---` + Markdown body. Directory name == `name`.

## Frontmatter

| field | req | constraint |
|---|---:|---|
| `name` | Y | 1..64 ASCII `[a-z0-9]`; single internal `-`; no edge/consecutive `-`; directory match |
| `description` | Y | string, 1..1024 chars; capability+trigger |
| `license` | N | short name or bundled license reference |
| `compatibility` | N | string, 1..500 chars; environment requirements |
| `metadata` | N | string->string map |
| `allowed-tools` | N | space-separated string; experimental/client-dependent |

Other top-level fields=extensions; portable only if current shared spec defines them.

## Body/resources

- target: `<500` lines, about `<5000` tokens; recommendation, not validity
- core path in `SKILL.md`; branch-only detail in JIT resources with explicit read trigger
- relative resources resolve from package root; installed/copied package retains all
- resources stay inside root absent explicit trusted external policy
- scripts: noninteractive flags/stdin/env; concise `--help`; meaningful exits/errors; structured output; runtime/deps declared

## Result classes

1. spec: layout, delimiters, YAML types, lengths, name syntax/match
2. integrity: links, containment, required files, deps, license
3. instruction: scope, relevant detail, decisions, done criteria, JIT disclosure
4. behavior: trigger precision + task output in real client
5. compatibility: optional fields/extensions/paths/tools/activation

`spec PASS` does not imply 2..5 PASS.
