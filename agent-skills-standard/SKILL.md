---
name: agent-skills-standard
description: "Audits Agent Skills packages and commits; implements client support. Use for skill create/update gates, package/spec/portability audits, catalog migration, or client discovery, activation, and resource loading. Don't use for third-party install/update, AGENTS.md rules, or session-friction mining."
compatibility: "scripts/audit-package.py: Python 3.11+ and PyYAML. Client work: target source/tests."
metadata:
  category: "agent-tooling"
  source: "https://agentskills.io/home"
  sourceVersion: "agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T11:28:53+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# Agent Skills standard

## 1. Route

- create: `skill-creator` -> 2,3,5,6
- revise: domain edit -> 2,3,5,6
- package audit: 2,3
- catalog migration: 2,3(all),4
- client implementation: 2,4,5
- repo commit with skill changes: 6
- third-party install/update: `npx skills`; STOP unless audit requested

## 2. Pin spec

1. READ current [spec](https://agentskills.io/specification).
2. RECORD immutable revision; compare `metadata.sourceVersion` (baseline only).
3. SEPARATE shared fields from client extensions (`context`, hooks, invocation controls).

## 3. Audit package

1. READ `references/package-spec.md`.
2. RUN:
   ```bash
   python3 scripts/audit-package.py path/to/skill
   skills-ref validate path/to/skill  # iff installed
   ```
3. CHECK: spec errors; package integrity; coherent scope; decisions; done criteria; progressive disclosure; root-relative resources.
4. Trigger/output concerns -> READ `references/evaluation.md`.
5. OUT: copy `assets/audit-report.md`; include package, spec revision, exact results, warnings, unverified clients.

## 4. Catalog/client

### Catalog migration

1. INVENTORY `(name, packageRoot, scope, source)` for every `SKILL.md`.
2. COLLISION: deterministic precedence; project > user; report winner+shadowed.
3. MOVE whole package, including referenced resources.
4. KEEP shared metadata values strings; client config outside shared frontmatter unless supported extension.
5. VALIDATE all packages+links; exercise discovery+activation per client.

### Client implementation

1. READ `references/client-lifecycle.md`.
2. DEFINE scopes+precedence+trust. Include `.agents/skills/` for interoperability.
3. BOUND scan roots/depth/count/size; skip VCS/dependencies/build/cache.
4. STRICT YAML first; diagnostics retained. Skip unparseable or empty-description package. Compatibility fallback only after strict failure.
5. DISCLOSE catalog only: `name`, `description`, activation locator/id.
6. ACTIVATE by file read or enum-constrained tool; return package root.
7. LOAD resources JIT; normalize path; enforce root containment+normal approvals.
8. SUPPORT explicit activation, list, diagnostics, reload, disable, trust.

## 5. Behavioral proof

1. Fresh client session: multiple valid packages + malformed fixture.
2. ASSERT startup=catalog metadata only; match loads intended body/resource once; near-miss no load.
3. ASSERT collision precedence+diagnostic; untrusted/invalid content never enters model context.
4. ASSERT missing resource, malformed YAML, empty description, symlink escape => actionable failure.
5. ASSERT reload handles add/change/delete. Measure catalog+activated size; enforce limits.
6. Trigger/output eval -> READ `references/evaluation.md`; compare with no-skill/previous baseline.

## 6. Commit gate

1. INSPECT status+full diff; enumerate created/changed/renamed/deleted packages+catalog effects.
2. RUN each changed package:
   ```bash
   python3 scripts/audit-package.py path/to/skill --strict
   ```
3. RUN repo metadata validator + local-link checker.
4. Catalog changed -> update it; RUN:
   ```bash
   npx skills add . --list
   ```
5. REQUIRE final-file behavioral proof.
6. CHECK metadata policy: `category` first; `source`, `sourceVersion`, `createdBy`, `createdAt`, `updatedBy`, `updatedAt`.
7. CHECK staged diff: secrets, generated/cache files, broken/untracked resources, unrelated edits.
8. COMMIT only after all pass; use repo convention.

## Fail

- spec newer than baseline -> read delta first
- PyYAML absent -> disposable install OR `skills-ref validate`; no line parser
- `skills-ref` != client -> report both; classify deliberate compatibility
- duplicate name -> no silent winner
- resource escapes root -> reject absent explicit trusted policy
- activation unobservable -> instrument before grading
- host cannot exercise path -> finish reachable checks; mark unverified
