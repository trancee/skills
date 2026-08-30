# Agent Skills client lifecycle

Source: [client integration](https://agentskills.io/client-implementation/adding-skills-support).

## Pipeline

1. DISCOVER
   - explicit project/user scopes; optional org/builtin/remote/configured
   - interoperability: `.agents/skills/` + client-native path
   - bound roots/depth/dir count/file size; skip VCS/deps/cache/build
   - trust-gate project packages before model exposure
2. PARSE
   - exact `SKILL.md`; real YAML parser; split frontmatter/body
   - store `name`,`description`,absolute activation locator,package root
   - strict first; fallback only known compatibility case + diagnostic
   - unparseable or empty `description` => skip
3. COLLIDE
   - key by declared `name`; project > user
   - define all provider precedence; filesystem order invalid
   - diagnostic includes winner+shadowed paths
4. DISCLOSE
   - startup only `name`,`description`,locator/id
   - omit disabled/unauthorized/invalid/unavailable
   - empty catalog => omit catalog instructions/tool
5. ACTIVATE
   - model selection + explicit user path
   - file read OR tool constrained to discovered-name enum
   - return body/full file + package root; preserve needed `compatibility`
   - stable origin wrapper if context manager tracks sources
6. RESOURCE
   - JIT only after instruction pointer
   - resolve against package root; normalize; containment check
   - normal sandbox/approval remains active
7. REFRESH/DIAGNOSE
   - define trigger: process/session/reload/watcher/config change
   - expose scope, winner, shadowed paths, validation errors, disabled state

## Tests

malformed YAML; missing description; collision; add/change/delete; symlink escape; untrusted project; empty catalog; unavailable activation; resource containment; reload.
