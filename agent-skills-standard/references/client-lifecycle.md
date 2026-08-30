# Agent Skills client lifecycle

Use this reference when adding Agent Skills support to an agent or development tool. The live source is [How to add skills support to your agent](https://agentskills.io/client-implementation/adding-skills-support).

## 1. Discover

Scan explicit project and user scopes. Add organization, built-in, remote, or configured scopes only when the client has them. For interoperability, scan `.agents/skills/` alongside the client-specific directory.

Bound traversal by allowed roots, depth, directory count, and file size. Skip `.git`, dependency directories, caches, and build output. Gate project-level packages on repository trust before parsing content for model use.

## 2. Parse

Split `SKILL.md` into YAML frontmatter and Markdown instructions. Parse YAML with a real YAML parser. Store at least `name`, `description`, and an absolute activation location. Retain the package root for relative resources.

Apply strict specification validation first. A compatibility parser may recover known malformed input after strict parsing fails, but it must emit a diagnostic. Skip an unparseable package or a package with no usable description.

## 3. Resolve collisions

Key the catalog by declared skill name. Project scope overrides user scope. Define precedence among client-native, shared, organization, configured, and built-in providers. Emit a warning that identifies both the winning and shadowed package.

Use one deterministic rule. Filesystem enumeration order is not a stable precedence rule.

## 4. Disclose the catalog

Put only selection metadata in startup context. Include `name`, `description`, and either the absolute location or an opaque identifier accepted by the activation tool.

Omit disabled, unauthorized, invalid, and unavailable packages. If the catalog is empty, omit the catalog instructions or activation tool rather than presenting an empty choice.

## 5. Activate

Support model-selected and user-explicit activation. Use one of two paths:

- Let a file-capable model read the selected `SKILL.md` from its disclosed location.
- Register a constrained activation tool that accepts only discovered names and returns the instructions.

Return the package root with activated content. If a dedicated tool strips frontmatter, preserve compatibility information needed at execution time. Wrap content with a stable skill identifier when context management needs to track its origin.

## 6. Load resources

Read scripts, references, and assets only after the activated instructions point to them. Resolve relative paths against the package root, normalize them, and enforce containment before reading or running a resource. Apply normal tool approval and sandbox rules to skill-directed actions.

## 7. Refresh and diagnose

Define when discovery refreshes: process start, session start, explicit reload, file watcher event, or configuration change. Expose a list or diagnostics command that shows source scope, winning path, shadowed packages, validation errors, and disabled state.

Test malformed YAML, missing descriptions, name collisions, deleted packages, changed files, symlink escapes, untrusted projects, empty catalogs, and unavailable activation targets.
