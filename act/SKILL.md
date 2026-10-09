---
name: act
description: "Installs, configures, runs, and troubleshoots nektos act for local GitHub Actions execution. Use when selecting workflows, events, jobs or matrix cells, configuring runner images and Docker access, supplying local inputs/secrets, or investigating differences from GitHub-hosted runs. Don't use for Arrange-Act-Assert testing, general Docker administration, or operating production GitHub runners."
compatibility: "Baseline: act 0.2.89. Container execution requires a reachable Docker Engine API; host execution requires the actual OS/toolchains and is not isolated. Podman is experimental, not a supported-equivalence guarantee. Event helper requires Python 3.9+; downloads and uncached actions/images require network access."
metadata:
  category: "development"
  source: "https://github.com/nektos/act"
  sourceVersion: "v0.2.89@4f411281417e88660bea1c1a1749aa71ae0bd60f; act-docs@35cab6107d2afb3269a61dc5de5c15c151a4574f; inspected 2026-10-09"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-09T11:18:41+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-09T11:18:41+02:00"
---

# act: local GitHub Actions

## Step 1: Bound the run

1. Identify the repository, workflow file, explicit event, job IDs, dependency jobs, matrix cells, host OS/architecture, and required toolchains. Read every selected job/action before execution, including reusable workflows and local actions.
2. Read `references/security-parity.md`. Treat workflow code as executable code with local file/network access; approve deployment, publication, destructive steps, and credential exposure separately from a local test.
3. Inspect invocation-directory/home/XDG act configuration and `.env`, `.vars`, `.input`, `.secrets` ownership without printing secret values. Existing config can add mounts, privileges, tokens, and flags even to an apparently narrow command.
4. Choose a disposable workspace and minimal non-production credentials. Prefer a container with its daemon socket mount disabled unless the reviewed job needs nested Docker. Host execution is an explicit non-isolated alternative, not a Docker failure fallback.

Gate: exact execution scope, transitive actions, side effects, configuration, and credential boundary are known.

## Step 2: Install and select the runner

1. Read `references/installation-runners.md`. Establish `act --version` and installed `act --help`; the released binary and pinned source take precedence over stale documentation snippets.
2. Container path -> verify Docker daemon/API access, select an image for each exact `runs-on` label with `-P`, and establish architecture/tool availability. macOS/Windows labels do not become those operating systems inside a Linux image.
3. Host path -> use `-P label=-self-hosted` only for reviewed code on a capable host; provision required shells/Node/toolchains. Keep host results distinct from container results.
4. Record image tag/digest and tool versions. Supply explicit platform mappings for unattended runs rather than accepting the first-run size prompt. Preserve existing version/config ownership.

Gate: the selected runner backend executes on the intended OS/architecture; every required label/tool has a deliberate mapping.

## Step 3: Select and prepare the event

1. Read `references/usage-events.md`. List before running; pair `-W` with `-j` to avoid matching the same job ID in unrelated files:
   ```bash
   act push -W .github/workflows/ci.yml --list
   act push -W .github/workflows/ci.yml -j test --graph
   ```
2. Always name the event. No-argument runs usually select push but can select the sole available event; `-j` plans a job and its dependencies rather than reproducing GitHub's entire trigger filtering.
3. Event-dependent conditions -> use a sanitized real payload or generate a minimal local payload from this skill:
   ```bash
   python3 scripts/make-event.py workflow_dispatch --input MESSAGE=local > local-event.json
   ```
   Read helper `--help`; it emits JSON with `act:true`, not a complete GitHub delivery. Add every field actually accessed by the workflow. Validate custom JSON with `python3 -m json.tool local-event.json`.
4. Supply inputs, repository vars, step env, and secrets through their distinct flags/files. Use secure prompt/inherited secret names or a protected ignored secret file; do not place real secret literals in arguments, logs, config, or committed assets. Act can discover a GitHub CLI token automatically; explicitly supply an empty GITHUB_TOKEN for credential-free runs.
5. Optional matrix narrowing -> repeat `--matrix axis:value` for existing combinations. Inspect logs to confirm a selected cell actually ran; exclusions or absent values can select nothing.

Gate: the plan, event values, config sources, and required contexts match the intended scenario without accidental token injection.

## Step 4: Plan, execute, and inspect

1. Validate schema/plan with `act --validate --strict -W path/to/workflow.yml`, list, and graph. For reviewed container runs, `-n` requests no container creation but is not a sandbox. **On act 0.2.89, host-runner steps execute even with `-n`** (observed); never use host dry-run as a no-execution safety gate. Planning/schema success does not prove runtime behavior or GitHub parity.
2. Execute one scoped scenario using an explicit runner mapping, event payload, and non-production credentials. For a container shell-only job:
   ```bash
   act workflow_dispatch -W .github/workflows/ci.yml -j test \
     -e local-event.json -P ubuntu-latest=catthehacker/ubuntu:act-latest \
     --container-daemon-socket=- -s GITHUB_TOKEN=
   ```
   Replace paths/label/image with the reviewed plan. Preserve exit status; verify expected steps, outputs, artifacts, and failures rather than accepting an empty plan or skipped job as success.
3. Artifact actions -> enable `--artifact-server-path` only when needed, choose a reachable address/port, and inspect downloaded files. Cache/image reuse is a separate branch; offline mode is not network isolation.
4. Fresh-copy run first. Use `--bind`, `--reuse`, watch mode, privileged mode, daemon exposure, or alternate network only when the scenario requires their changed state/security semantics.
5. New setup proof -> copy `assets/smoke.yml` into a disposable repository as `.github/workflows/local-smoke.yml`. Follow the exact fixture commands in `references/usage-events.md`, selecting flavor:beta and supplying MESSAGE, public LOCAL_PROBE sentinel, and CHANNEL. The workflow checks matrix selection, context values, step/job output propagation, and an observable result. Do not install this fixture into the consumer's production CI by default.

Gate: the intended job/cells and dependency path actually executed; expected values/artifacts and a relevant failure path were observed.

## Step 5: Resolve gaps and report

1. Locate the first failed boundary: event/selection, runner image/tool, engine/mount, action source/checkout, secret/context, or application command. Use focused corrections in the owning workflow/config; avoid blanket cache wipes and hidden local-only bypasses.
2. Read `references/security-parity.md` for GitHub-only features. Keep actual GitHub verification for permissions/OIDC, environment approvals/secrets, concurrency/cancellation, hosted OS/tool images, and cross-run services. Local success is not a CI green claim.
3. Copy `assets/run-report.md`; record act/source version, effective config, exact event/job/matrix, runner image/host, non-secret context sources, exit/output/artifact evidence, and unverified parity. Redact diagnostics before sharing.

## Error Handling

- Missing act/daemon/architecture/tool -> follow `references/installation-runners.md`; repair the evidenced prerequisite rather than silently running on the host.
- No stages, skipped cells, unexpected job -> name the event, check `-W`, job ID/needs, event conditions, and matrix exclusions; compare list/graph with actual logs.
- Missing input/var/secret or auth failure -> follow `references/usage-events.md`; distinguish contexts and token availability from GitHub permission enforcement.
- Missing artifact/cache URL -> enable the appropriate local service and prove runner reachability; do not claim cross-run GitHub behavior.
- Event helper error -> correct required event arguments/KEY=VALUE format; stdout is JSON, stderr is actionable diagnostics.
- Local success/GitHub failure -> compare documented parity gaps and actual hosted runner evidence before modifying application behavior.
