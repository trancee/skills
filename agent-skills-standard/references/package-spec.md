# Agent Skills package specification

Use this reference for package audits. Re-read the live [Agent Skills specification](https://agentskills.io/specification) before changing validation behavior.

## Required layout

A package is a directory that contains `SKILL.md`. The filename is case-sensitive. `scripts/`, `references/`, `assets/`, and other package resources are optional.

`SKILL.md` contains YAML frontmatter between opening and closing `---` lines, followed by Markdown instructions. The package directory name must match the frontmatter `name`.

## Shared frontmatter

| Field | Required | Type and constraints |
| --- | --- | --- |
| `name` | Yes | String of 1 to 64 lowercase ASCII letters, digits, or single hyphens. No leading, trailing, or consecutive hyphens. Must match the package directory. |
| `description` | Yes | Non-empty string of at most 1024 characters. State what the skill does and when it applies. |
| `license` | No | Short license name or reference to a bundled license file. |
| `compatibility` | No | Non-empty string of at most 500 characters describing environment requirements. |
| `metadata` | No | Mapping from string keys to string values. |
| `allowed-tools` | No | Space-separated string of pre-approved tools. This field is experimental and client support varies. |

Treat additional top-level fields as extensions. Preserve them only when the target clients define their behavior. Do not label an extension as portable shared metadata.

## Instructions and resources

Keep the main instructions below 500 lines and about 5,000 tokens when practical. These are recommendations, not frontmatter validity rules. Move branch-specific detail to package resources and state exactly when the agent should load each file.

Resolve relative file references from the package root. Keep referenced resources inside that root unless the client has a separate trusted external-resource policy. A copied or installed package must retain every referenced file.

Scripts must expose non-interactive inputs, concise `--help`, meaningful exit codes, useful errors, and structured output where another tool consumes the result. Document runtime and dependency requirements in the script or `compatibility` field.

## Validation layers

Separate these results:

1. **Specification validity:** layout, frontmatter delimiters, YAML types, field lengths, name syntax, and directory match.
2. **Package integrity:** local links, resource containment, required files, script dependencies, and licenses.
3. **Instruction quality:** coherent scope, relevant detail, progressive disclosure, decision points, and completion criteria.
4. **Behavior:** trigger precision and task output measured in a real client.
5. **Client compatibility:** support for optional fields, extensions, installation paths, tools, and activation controls.

A package can pass the specification and still fail instruction quality, behavior, or one client.
