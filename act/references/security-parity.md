# Trust and GitHub parity

## Local workflows are real code

Review run commands, remote/local/composite/Docker actions, reusable workflows, needs dependencies, and matrix expansion before execution. A workflow can publish, delete, deploy, or read credentials on a local run exactly as on CI. Event labels and act=true are not a sandbox.

Keep host execution (`-P label=-self-hosted`) for trusted code in disposable workspaces; it runs with the invoking identity and installed tools. Container execution also carries risks: supplied secrets, network access, bind mounts, daemon socket, privileged/capability options, and host-network defaults. Disable daemon mounting unless needed, avoid unnecessary privileges, and explicitly choose safe storage/credentials. Docker socket access is effectively daemon/host control.

`.actrc` can inherit sensitive arguments and mounts. Do not store secrets there. `.secrets` and `.env` may be copied or mounted if not excluded; keep credential files protected/ignored or outside the workspace. Even a list/validation command loads configuration and secret sources in the CLI path. For a credential-free smoke, isolate home/config and supply an empty GITHUB_TOKEN rather than letting act discover existing GitHub CLI credentials.

Leave `--insecure-secrets` off. Verbose/JSON/bug-report logs can contain paths, config, context, URLs, and echoed commands; redact before sharing. Do not assume log masking protects transformed secret values, artifacts, or network requests. Pin actions/images according to repo policy and review substitutions.

## What local success does not prove

The canonical docs are an older snapshot than the released binary. Treat their [unsupported functionality list](https://nektosact.com/not_supported.html) as a parity checklist; verify source/actual behavior for the selected version when a specific feature matters.

| Boundary | Required verification |
| --- | --- |
| Hosted runner tools/OS | Actual image digest and installed tools; GitHub-hosted execution for OS/SDK-specific behavior |
| Event filters/context | Real event delivery, branches/paths/action type, repository/sender/SHA fields; local payload only covers supplied values |
| Permissions/GITHUB_TOKEN | GitHub per-run scope and enforcement; a supplied PAT is not scoped by local job.permissions |
| OIDC | GitHub issuer/token request integration; act's local environment is not an OIDC provider |
| Deployment environments | GitHub approvals, environment-scoped secrets, protections; local secrets flatten that distinction |
| Concurrency/timeouts/cancellation | Real GitHub orchestration; CLI worker limits are not workflow concurrency groups |
| Artifacts/cache | Real remote retention, scope, cross-run/repository access and service availability |
| Summaries/annotations/matchers | GitHub UI behavior; step logs or local files alone don't prove it |
| Filesystem/state | Clean checkout/image versus copied uncommitted files, bind/reused workspaces, cached actions |

The docs specifically list ignored concurrency/run-name, job permissions/environment/timeout/continue-on-error, incomplete github context, missing OIDC URL, unprocessed summaries/matchers/annotations, and incomplete cancellation. Do not claim these are fully implemented merely because the YAML parses. Also do not delete a feature from production workflows just to make act green. Record the divergence and keep a remote verification requirement; consult pinned source when diagnosing one of those details.

## Failure routing

- **No stages / wrong workflow**: inspect event, exact workflow file, job ID and needs. A selected job can bypass trigger filtering; validate local scenario separately from GitHub dispatch.
- **Skipped job / empty matrix**: inspect condition inputs, ACT/local act marker, excludes and requested values; demand evidence of executed steps.
- **Missing binary/Node/module**: inspect runner image/host tool versions, copied gitignored files, local action build output, checkout paths. Prefer explicit setup steps or a deliberate image over the largest image by default.
- **Socket/mount/network error**: check act's DOCKER_HOST, API access, daemon-side paths and container reachability. Podman success/failure is experimental backend evidence.
- **Unexpected stale code**: inspect checkout substitution, action ref/digest, cache, --reuse and --bind; fix owned inputs rather than wiping global caches.
- **Auth/context failure**: inspect secret names/sources, GitHub Enterprise host and actual token policy without printing credentials. Reproduce the smallest authorized call.
- **Local green / remote red**: compare event, runner tools, OS, token scope, orchestration, checkout and services. Keep the application failure visible; avoid a local-only bypass unless it is the requested test boundary.

Sources: [act guide](https://nektosact.com/), [unsupported features](https://nektosact.com/not_supported.html), [source release](https://github.com/nektos/act/tree/4f411281417e88660bea1c1a1749aa71ae0bd60f), [docs snapshot](https://github.com/nektos/act-docs/tree/35cab6107d2afb3269a61dc5de5c15c151a4574f).
