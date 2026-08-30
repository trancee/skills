---
name: agent-skills-standard
description: "Audits Agent Skills packages, gates skill repository commits, and implements Agent Skills support in agent clients. Use when creating or updating a skill, validating a skill repository before commit, checking an existing SKILL.md directory against agentskills.io, reviewing portability and progressive disclosure, migrating a skill catalog, or adding discovery and activation to an agent. Don't use for installing third-party skills, editing AGENTS.md rules, or mining session friction."
compatibility: "Requires Python 3.11+ and PyYAML for scripts/audit-package.py; client integration requires the target client source and test tooling."
metadata:
  category: "agent-tooling"
  source: "https://agentskills.io/home"
  sourceVersion: "agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T11:28:53+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:37:12+02:00"
---

# Agent Skills standard

Audit new and existing skill packages, gate skill repository commits, and add standards-compatible skill support to agent clients. Use `skill-creator` for domain authoring. Run this skill during creation or revision and again before commit to check the shared format and repository integration.

## Procedures

**Step 1: Choose the standards task**

1. Classify the request as new skill creation, skill revision, package audit, catalog migration, portability review, client implementation, or repository commit.
2. For a new skill, invoke `skill-creator` and complete its authoring workflow. Then return to Steps 2, 3, 7, and 8 of this workflow before committing.
3. For an existing skill revision, apply the requested domain change, then run Steps 2, 3, 7, and 8 before committing.
4. For a repository commit that contains skill changes, identify every created, changed, renamed, or deleted package, then continue to Step 8.
5. For third-party skill installation or refresh, use the `skills` CLI and stop this workflow unless the user also requests an audit.
6. For a package audit, continue to Step 2 and then Step 3.
7. For a catalog migration, continue to Step 2, audit every package with Step 3, then apply Step 4.
8. For client implementation, continue to Step 2 and then Step 5.

**Step 2: Pin the governing specification**

1. Read the current [Agent Skills specification](https://agentskills.io/specification) before changing validation or client behavior.
2. Record the specification repository commit or another immutable source revision.
3. Compare that revision with `metadata.sourceVersion`. Treat this skill's recorded revision as its authoring baseline, not as the latest specification.
4. Identify client-specific extensions separately. Never present an extension such as `context`, hooks, or invocation controls as part of the shared specification unless the current specification defines it.

**Step 3: Audit a skill package**

1. Read `references/package-spec.md`.
2. Run the bundled audit:

   ```bash
   python3 scripts/audit-package.py path/to/skill
   ```

3. If the checked-out `skills-ref` reference library is available, run its validator too:

   ```bash
   skills-ref validate path/to/skill
   ```

4. Resolve every error against the current specification. Treat bundled-script recommendations, line-count guidance, and portability findings as warnings unless a client makes them mandatory.
5. Inspect the body for a coherent task, clear decision points, completion criteria, progressive disclosure, and relative resource paths.
6. Compare the `description` with realistic matching and near-miss prompts. Read `references/evaluation.md` when trigger behavior or output quality is in scope.
7. Copy `assets/audit-report.md` and record the exact package, source revision, validator output, warnings, and unverified client behavior.

**Step 4: Migrate a skill catalog**

1. Inventory every discovered `SKILL.md`, its package root, source scope, and declared `name`.
2. Reject duplicate names until the catalog defines deterministic precedence. Project packages should override user packages; document any additional same-scope rule.
3. Preserve each complete package. Move `SKILL.md`, `scripts/`, `references/`, `assets/`, and other referenced resources together.
4. Keep shared metadata as string values. Store client-only configuration outside shared frontmatter unless the client explicitly supports that extension.
5. Validate every package after movement and check every local resource link.
6. Exercise discovery and activation in each supported client. File presence alone does not prove that a client discloses or loads the skill.

**Step 5: Implement client support**

1. Read `references/client-lifecycle.md` before changing client code.
2. Define project, user, organization, built-in, and configured scopes. Include `.agents/skills/` when cross-client interoperability is required.
3. Gate untrusted project packages before their instructions reach the model.
4. Discover package directories under explicit depth and directory-count limits. Skip build output, dependency trees, and version-control internals.
5. Parse strict YAML frontmatter and preserve diagnostics. Skip packages without a usable `description`; apply any lenient compatibility fallback only after strict parsing fails.
6. Resolve duplicate names with deterministic scope and provider precedence. Surface shadowing diagnostics.
7. Disclose only the catalog fields required for selection, normally `name`, `description`, and an activation location or identifier.
8. Activate a selected skill by loading its instructions through a file read or a constrained activation tool. Include the package root so relative resources resolve correctly.
9. Load referenced scripts, references, and assets only when instructions require them.
10. Add explicit user activation, listing, diagnostics, reload, disable, and trust behavior appropriate to the client.

**Step 6: Verify progressive disclosure and safety**

1. Start a clean client session with multiple valid skills and one malformed fixture.
2. Confirm that startup context contains catalog metadata, not every full skill body.
3. Confirm that a matching request loads one intended `SKILL.md` and resolves one relative resource from its package root.
4. Confirm that a near-miss request does not load the skill.
5. Confirm that a duplicate name follows documented precedence and emits a diagnostic.
6. Confirm that an untrusted project cannot inject skill instructions before trust is granted.
7. Confirm that a missing resource, malformed YAML document, empty description, and escaped symlink fail with actionable diagnostics.
8. Measure the catalog and activated instruction size. Enforce client limits before prompt construction.

**Step 7: Evaluate behavior and report**

1. Read `references/evaluation.md` for package trigger or output evaluation.
2. Compare client behavior with and without the skill, or compare the new client path with the previous version.
3. Require observable evidence for discovery, activation, resource loading, task output, and failure handling.
4. Record specification revision, client version, scopes, precedence, trust policy, parser behavior, prompt shape, tests, and remaining extensions in `assets/audit-report.md`.
5. Report shared-spec compliance and client-specific compatibility separately.

**Step 8: Gate a skill repository commit**

1. Inspect version-control status and the complete diff. Identify every created, changed, renamed, or deleted `SKILL.md` package and every catalog entry affected by those changes.
2. Run the strict bundled audit for each created or changed package:

   ```bash
   python3 scripts/audit-package.py path/to/skill --strict
   ```

3. Run the repository's metadata validator and local-link checker for every affected package. Resolve all failures before staging.
4. If a skill was added, renamed, or deleted, update the repository catalog and confirm discovery:

   ```bash
   npx skills add . --list
   ```

5. Require current behavioral proof for changed procedures and scripts. Reuse evidence from the creation or revision run only when it covers the final files.
6. Confirm that `category` remains first under `metadata`; confirm `source`, `sourceVersion`, `createdBy`, `createdAt`, `updatedBy`, and `updatedAt` follow repository policy.
7. Inspect the staged diff for secrets, generated output, caches, broken resource paths, untracked package files, and unrelated changes.
8. Commit only after package audits, discovery, links, metadata, behavior checks, and the staged diff pass. Use the repository's commit-message convention.

## Error Handling

- If the specification source changed after `metadata.sourceVersion`, read the changed specification before modifying code or package rules.
- If PyYAML is unavailable, install it in a disposable environment or run `skills-ref validate`; do not replace YAML parsing with line-based production logic.
- If `skills-ref` and a client disagree, report both results and determine whether the client deliberately accepts nonstandard input.
- If two packages declare one name, stop silent discovery and apply the documented precedence rule with a warning.
- If a package resource resolves outside its package root, reject the path unless the client has an explicit trusted-resource policy.
- If an eval cannot observe activation, add client instrumentation before judging trigger quality.
- If a client cannot exercise a scope or activation method in the current environment, finish package validation and name the unverified behavior.
